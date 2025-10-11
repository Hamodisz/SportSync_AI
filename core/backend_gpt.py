# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
Sport identity recommendations (3 cards) with Layer-Z, first-week (qualitative),
and VR/no-VR variants. Arabic/English.

Pipeline (واقعي أولاً):
1) Evidence Gate (يرفض إن كانت الإجابات غير كافية ويعيد أسئلة متابعة)
2) تحليل واقعي من قاعدة المعرفة (priors + trait_links + guards + templates)
3) LLM كآخر خيار (fallback) إن ما كفت القاعدة + إصلاح JSON عند اللزوم
4) Hard de-dup + URL scrub + Telemetry + قفل ملف للـ blacklist (thread/process-safe)

قواعد ثابتة:
- ممنوع ذكر الوقت/التكلفة/العدّات/الجولات/المكان المباشر.
- يُسمح بأسماء الرياضات إذا ALLOW_SPORT_NAMES=True
- dedupe محلي وعالمي عبر data/blacklist.json
"""

from __future__ import annotations

import os, json, re, hashlib, importlib, time, random
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# ========= Job Manager (اختياري) =========
try:
    from core.job_manager import create_job, read_job, update as job_update, run_in_thread
except Exception:
    def create_job(meta: Optional[dict] = None): return {"id": "nojob", "status": "error"}
    def read_job(job_id: str): return None
    def job_update(job_id: str, **kw): pass
    def run_in_thread(job_id: str, target, *args, **kwargs): return None

def _job_note(job_id: str,
              progress: Optional[int] = None,
              note: Optional[str] = None,
              status: Optional[str] = None) -> None:
    if not job_id:
        return
    try:
        payload: Dict[str, Any] = {}
        if progress is not None: payload["progress"] = int(progress)
        if note: payload["note"] = note
        if status: payload["status"] = status
        if payload:
            job_update(job_id, **payload)
    except Exception as e:
        print(f"[JOB_NOTE][WARN] {e}")

# ========= LLM Client (OpenAI-compatible عبر طبقة مفصولة) =========
try:
    from core.llm_client import make_llm_client, pick_models, chat_once
except Exception as e:
    raise RuntimeError("ملف core/llm_client.py مفقود أو فيه خطأ. تأكد من إضافته.") from e

LLM_CLIENT = make_llm_client()
try:
    CHAT_MODEL, CHAT_MODEL_FALLBACK = pick_models()  # يرجّع Tuple
except Exception:
    _models = pick_models()
    CHAT_MODEL = getattr(_models, "get", lambda *_: None)("main")
    CHAT_MODEL_FALLBACK = getattr(_models, "get", lambda *_: None)("fallback")

print(f"[BOOT] LLM READY? {'YES' if LLM_CLIENT else 'NO'} | main={CHAT_MODEL} fb={CHAT_MODEL_FALLBACK}")

# ========= App Config =========
try:
    from core.app_config import get_config
    CFG = get_config()
except Exception:
    CFG = {}

ALLOW_SPORT_NAMES = (CFG.get("recommendations") or {}).get("allow_sport_names", True)

REC_RULES = CFG.get("recommendations") or {}
_MIN_CHARS = int(REC_RULES.get("min_chars", 220))
_REQUIRE_WIN = bool(REC_RULES.get("require_win_condition", True))
_MIN_CORE_SKILLS = int(REC_RULES.get("min_core_skills", 3))

# ========= Runtime Guards / Tunables =========
REC_BUDGET_S = float(os.getenv("REC_BUDGET_S", "22"))
REC_REPAIR_ENABLED = os.getenv("REC_REPAIR_ENABLED", "1") == "1"
REC_FAST_MODE = os.getenv("REC_FAST_MODE", "0") == "1"
REC_DEBUG = os.getenv("REC_DEBUG", "0") == "1"
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "6000"))

def _dbg(msg: str) -> None:
    if REC_DEBUG:
        print(f"[RECDBG] {msg}")

def _warn(msg: str) -> None:
    print(f"[WARN] {msg}")

def _err(msg: str) -> None:
    print(f"[ERROR] {msg}")

# Evidence Gate thresholds (defaults if not provided)
EGCFG = (CFG.get("analysis") or {}).get("egate", {}) if isinstance(CFG.get("analysis"), dict) else {}
_EG_MIN_ANSWERS = int(EGCFG.get("min_answered", 3))
_EG_MIN_TOTAL_CHARS = int(EGCFG.get("min_total_chars", 120))
_EG_REQUIRED_KEYS = list(EGCFG.get("required_keys", []))

# ========= DataPipe (Zapier/Webhook/Disk) =========
try:
    from core.data_pipe import get_pipe
    _PIPE = get_pipe()
except Exception:
    _PIPE = None

# ========= Security scrubber =========
try:
    from core.security import scrub_unknown_urls
except Exception:
    def scrub_unknown_urls(text_or_card: str, cfg: Dict[str, Any]) -> str:
        return text_or_card

# ========= Evidence Gate (external) + fallback =========
try:
    from core.evidence_gate import evaluate as egate_evaluate
except Exception:
    egate_evaluate = None

# ========= Paths / Data =========
try:
    HERE = Path(__file__).resolve().parent
except NameError:
    HERE = Path.cwd()
ROOT = HERE.parent if HERE.name == "core" else HERE
DATA_DIR = (ROOT / "data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

BL_PATH = DATA_DIR / "blacklist.json"
KB_PATH = DATA_DIR / "sportsync_knowledge.json"
AL_PATH = DATA_DIR / "labels_aliases.json"

# ========= File Lock (race-safe) =========
try:
    from filelock import FileLock, Timeout
    FILELOCK_OK = True
except Exception:
    FILELOCK_OK = False

# ========= Helpers: Files =========
def _load_json_safe(p: Path) -> dict:
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_json_atomic(p: Path, payload: dict) -> None:
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(p)

# ========= Load KB / Aliases / Guards =========
KB = _load_json_safe(KB_PATH)
_ALIAS_MAP: Dict[str, str] = {}
if isinstance(KB.get("label_aliases"), dict):
    for canon, alist in KB["label_aliases"].items():
        for a in alist:
            _ALIAS_MAP[re.sub(r"\s+", " ", a.strip().lower())] = canon

AL2 = _load_json_safe(AL_PATH)
if isinstance(AL2.get("canonical"), dict):
    for a, canon in AL2["canonical"].items():
        _ALIAS_MAP[re.sub(r"\s+", " ", a.strip().lower())] = canon

KB_PRIORS: Dict[str, float] = dict(KB.get("priors") or {})
TRAIT_LINKS: Dict[str, Dict[str, float]] = dict(KB.get("trait_links") or {})
GUARDS: Dict[str, Any] = dict(KB.get("guards") or {})
HIGH_RISK_SPORTS: set = set(GUARDS.get("high_risk_sports", []) or [])
KB_ZI: Dict[str, Dict[str, List[str]]] = dict(KB.get("z_intent_keywords") or {})

_FORBIDDEN_GENERIC = set(
    KB.get("guards", {}).get("forbidden_generic_labels", [])
) | set(AL2.get("forbidden_generic", []) or [])

# ========= Arabic normalization =========
_AR_DIAC_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
_AR_MAP = str.maketrans({
    "\u0623": "\u0627", "\u0625": "\u0627", "\u0622": "\u0627",
    "\u0624": "\u0648", "\u0626": "\u064A", "\u0629": "\u0647", "\u0649": "\u064A",
})
def _normalize_ar(t: str) -> str:
    if not t: return ""
    t = _AR_DIAC_RE.sub("", t)
    t = t.translate(_AR_MAP)
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ========= Text normalizer =========
def _norm_text(val: Any) -> str:
    if val is None: return ""
    if isinstance(val, str): return val
    if isinstance(val, (list, tuple)):
        flat: List[str] = []
        for x in val:
            if isinstance(x, (list, tuple)):
                flat.extend(map(str, x))
            else:
                flat.append(str(x))
        return "، ".join([s.strip() for s in flat if s and str(s).strip()])
    if isinstance(val, dict):
        for k in ("text", "desc", "value", "answer"):
            if k in val and isinstance(val[k], str):
                return val[k]
        return json.dumps(val, ensure_ascii=False)
    return str(val)

# ========= Caches (soft) =========
try:
    from core.memory_cache import get_cached_personality, save_cached_personality
except Exception:
    _PERS_CACHE: Dict[str, str] = {}
    def get_cached_personality(analysis: Dict[str, Any], lang: str = "العربية") -> Optional[str]:
        key = f"{lang}:{hash(json.dumps(analysis, ensure_ascii=False, sort_keys=True))}"
        return _PERS_CACHE.get(key)
    def save_cached_personality(analysis: Dict[str, Any], personality: str, lang: str = "العربية") -> None:
        key = f"{lang}:{hash(json.dumps(analysis, ensure_ascii=False, sort_keys=True))}"
        _PERS_CACHE[key] = personality

try:
    from core.memory_cache import get_cached_recommendation, save_cached_recommendation  # type: ignore
except Exception:
    _REC_CACHE: Dict[str, List[str]] = {}
    def _answers_fingerprint(answers: Dict[str, Any], lang: str) -> str:
        try:
            blob = json.dumps(answers or {}, ensure_ascii=False, sort_keys=True)
        except Exception:
            blob = str(answers)
        h = hashlib.sha256((lang + "::" + blob).encode("utf-8")).hexdigest()[:24]
        return h
    def get_cached_recommendation(user_id: str, answers: Dict[str, Any], lang: str) -> Optional[List[str]]:
        key = f"{user_id}:{_answers_fingerprint(answers, lang)}"
        return _REC_CACHE.get(key)
    def save_cached_recommendation(user_id: str, answers: Dict[str, Any], lang: str, cards: List[str]) -> None:
        key = f"{user_id}:{_answers_fingerprint(answers, lang)}"
        _REC_CACHE[key] = list(cards or [])

# ========= User analysis imports =========
def _call_analyze_user_from_answers(user_id: str, answers: Dict[str, Any], lang: str) -> Dict[str, Any]:
    try:
        from analysis.user_analysis import analyze_user_from_answers as _ana
        try:
            out = _ana(user_id=user_id, answers=answers, lang=lang)
        except TypeError:
            out = _ana(answers)
        return {"traits": out} if isinstance(out, list) else (out or {})
    except Exception:
        try:
            from core.user_analysis import analyze_user_from_answers as _ana2
            try:
                out = _ana2(user_id=user_id, answers=answers, lang=lang)
            except TypeError:
                out = _ana2(answers)
            return {"traits": out} if isinstance(out, list) else (out or {})
        except Exception as e:
            _warn(f"user_analysis missing: {e}")
            return {"quick_profile": "fallback", "raw_answers": answers}

try:
    from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    try:
        from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
    except Exception:
        def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
            return ["إنجازات قصيرة", "نفور من التكرار", "تفضيل تحدّي ذهني"]

# ========= Signals & Intent =========
def _lang_key(lang: str) -> str:
    return "ar" if (lang or "").startswith("الع") else "en"

def _extract_signals(answers: Dict[str, Any], lang: str) -> Dict[str, int]:
    """
    يجمع كل إجابات المستخدم (أي نوع) كسلسلة نصية موحّدة (AR-normalized + lowercase)
    ثم يبحث عن كلمات دالة (بالعربي/الإنجليزي) بحسب z_intent_keywords من الـKB مع بعض الافتراضات.
    """
    # 1) طبيع كل القيم لنص
    parts: List[str] = []
    for v in (answers or {}).values():
        vv = v.get("answer") if isinstance(v, dict) and "answer" in v else v
        parts.append(_norm_answer_value(vv))   # يحوّل القوائم إلى "a, b, c" تلقائياً

    blob = " ".join(parts) if parts else ""
    blob_l = blob.lower()
    blob_n = _normalize_ar(blob_l)  # يحذف التشكيل ويوحّد الألف/التاء المربوطة.. إلخ

    res: Dict[str, int] = {}
    zi = KB_ZI.get(_lang_key(lang), {}) or {}

    # 2) دالة مساعدة للبحث عن أي كلمة من قائمة
    def any_kw(keys: List[str]) -> bool:
        if not keys: 
            return False
        for k in keys:
            k_norm = _normalize_ar(str(k).lower())
            if (k_norm and (k_norm in blob_n)) or (str(k).lower() in blob_l):
                return True
        return False

    # 3) قوائم افتراضية صغيرة (نضيف صيغ إملائية شائعة)
    vr_keys = zi.get("VR", []) + ["vr", "virtual reality", "headset", "واقع افتراضي", "الواقع الافتراضي", "نظاره", "نظارة"]
    prec_keys = zi.get("دقة/تصويب", []) + zi.get("Precision", []) + ["precision","aim","نشان","دقه","تصويب","دقة"]
    stealth_keys = zi.get("تخفّي", []) + zi.get("Stealth", []) + ["stealth","ظل","تخفي","اختباء"]
    combat_keys = zi.get("قتالي", []) + zi.get("Combat", []) + ["قتال","مبارزه","اشتباك","combat"]
    puzzles_keys = zi.get("ألغاز/خداع", []) + zi.get("Puzzles/Feint", []) + ["puzzle","لغز","ألغاز","خدعه","خداع"]
    solo_keys = zi.get("فردي", []) + ["solo","وحيد","لوحدي","فردي"]
    team_keys = zi.get("جماعي", []) + ["team","group","فريق","جماعي","تعاوني"]
    calm_keys = zi.get("هدوء/تنفّس", []) + zi.get("Calm/Breath", []) + ["breath","calm","هدوء","تنفس"]
    adren_keys = zi.get("أدرينالين", []) + zi.get("Adrenaline", []) + ["fast","rush","اندفاع","أدرينالين"]

    # 4) الاستخراج
    if any_kw(vr_keys):       res["vr"] = 1
    if any_kw(prec_keys):     res["precision"] = 1
    if any_kw(stealth_keys):  res["stealth"] = 1
    if any_kw(combat_keys):   res["combat"] = 1
    if any_kw(puzzles_keys):  res["puzzles"] = 1
    if any_kw(solo_keys):     res["solo_pref"] = 1
    if any_kw(team_keys):     res["team_pref"] = 1
    if any_kw(calm_keys):     res["breath"] = 1; res["calm"] = 1
    if any_kw(adren_keys):    res["high_agg"] = 1

    return res

def _call_analyze_intent(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
    # جرّب تنفيذ analyze_user_intent من أي طبقة متوفرة
    for modpath in ("core.layer_z_engine", "analysis.layer_z_engine"):
        try:
            mod = importlib.import_module(modpath)
            if hasattr(mod, "analyze_user_intent"):
                return list(mod.analyze_user_intent(answers, lang=lang) or [])
        except Exception:
            pass

    # fallback باستخدام الإشارات
    intents = set()
    sig = _extract_signals(answers, lang)
    if sig.get("vr"):         intents.add("VR")
    if sig.get("stealth"):    intents.add("تخفّي")
    if sig.get("puzzles"):    intents.add("ألغاز/خداع")
    if sig.get("precision"):  intents.add("دقة/تصويب")
    if sig.get("combat"):     intents.add("قتالي")
    if sig.get("solo_pref"):  intents.add("فردي")
    if sig.get("team_pref"):  intents.add("جماعي")
    if sig.get("breath"):     intents.add("هدوء/تنفّس")
    if sig.get("high_agg"):   intents.add("أدرينالين")
    return list(intents)
    
# ========= Optional encoder =========
def _extract_profile(answers: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    prof = answers.get("profile") if isinstance(answers, dict) else None
    if isinstance(prof, dict): return prof
    encode_answers = None
    try:
        from core.answers_encoder import encode_answers as _enc
        encode_answers = _enc
    except Exception:
        try:
            from analysis.answers_encoder import encode_answers as _enc
            encode_answers = _enc
        except Exception:
            encode_answers = None
    if encode_answers is None:
        return None
    try:
        enc = encode_answers(answers, lang=lang)
        preferences = enc.get("prefs", enc.get("preferences", {}))
        z_markers = enc.get("z_markers", [])
        signals   = enc.get("signals", [])
        hints = " | ".join([*z_markers, *signals])[:1000]
        return {
            "scores": enc.get("scores", {}),
            "axes": enc.get("axes", {}),
            "preferences": preferences,
            "hints_for_prompt": hints,
            "vr_inclination": enc.get("vr_inclination", 0),
            "confidence": enc.get("confidence", 0.0),
            "signals": signals,
            "z_markers": z_markers
        }
    except Exception as e:
        _warn(f"answers_encoder failed: {e}")
        return None

# ========= Evidence Gate (fallback) =========
def _norm_answer_value(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, dict):
        if "answer" in v: return str(v.get("answer") or "")
        if "value" in v: return str(v.get("value") or "")
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return ", ".join(map(str, v))
    return str(v)

def _egate_fallback(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    if not isinstance(answers, dict) or not answers:
        status = "fail"; total_chars = 0; answered = 0
    else:
        vals = [_norm_answer_value(v) for v in answers.values() if str(v).strip()]
        total_chars = sum(len(s.strip()) for s in vals)
        answered = sum(1 for s in vals if len(s.strip()) >= 3)
        if _EG_REQUIRED_KEYS:
            if any(not _norm_answer_value(answers.get(k, "")).strip() for k in _EG_REQUIRED_KEYS):
                status = "fail"
            else:
                status = "pass" if (answered >= _EG_MIN_ANSWERS and total_chars >= _EG_MIN_TOTAL_CHARS) else "borderline"
        else:
            if answered == 0 or total_chars < 40:
                status = "fail"
            elif answered < _EG_MIN_ANSWERS or total_chars < _EG_MIN_TOTAL_CHARS:
                status = "borderline"
            else:
                status = "pass"

    followups = (
        [
            "تفضّل اللعب: فردي أم جماعي؟ ولماذا بسطر واحد.",
            "تميل لهدوء وانسياب أم أدرينالين وقرارات خاطفة؟",
            "تحب دقّة/تصويب أم ألغاز/خداع بصري أثناء الحركة؟"
        ] if lang == "العربية" else [
            "Do you prefer solo or team play — and why, in one short line?",
            "Do you want calm/flow or adrenaline/snap decisions?",
            "Are you more into precision/aim or puzzles/visual feints in motion?"
        ]
    )
    return {
        "status": "fail" if answered == 0 or total_chars < 40 else status,
        "answered": int(answered),
        "total_chars": int(total_chars),
        "required_missing": [k for k in _EG_REQUIRED_KEYS if not _norm_answer_value((answers or {}).get(k, "")).strip()],
        "followup_questions": followups[:3]
    }

def _run_egate(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    if callable(egate_evaluate):
        try:
            res = egate_evaluate(answers=answers, lang=lang, cfg=EGCFG)
            if isinstance(res, dict) and "status" in res:
                return res
        except Exception as e:
            _warn(f"egate external failed: {e}")
    return _egate_fallback(answers, lang=lang)

def _format_followup_card(followups: List[str], lang: str) -> str:
    head = "🧭 نحتاج إجابات قصيرة قبل التوصية" if lang == "العربية" else "🧭 I need a few quick answers first"
    tips = "اكتب سطر واحد لكل سؤال." if lang == "العربية" else "One short line per question."
    lines = [head, "", tips, ""]
    for q in followups: lines.append(f"- {q}")
    lines.append("")
    lines.append("أرسل إجاباتك وسنقترح هوية رياضية واضحة فورًا." if lang == "العربية"
                 else "Send your answers and I’ll propose a clear sport-identity right away.")
    return "\n".join(lines)

# ========= Rules & helpers =========
_BLOCKLIST_AR = r"(جري|ركض|سباحة|كرة|قدم|سلة|طائرة|تنس|ملاكمة|كاراتيه|كونغ فو|يوجا|يوغا|بيلاتس|رفع|أثقال|تزلج|دراج|دراجة|ركوب|خيول|باركور|جودو|سكواش|بلياردو|جولف|كرة طائرة|كرة اليد|هوكي|سباق|ماراثون|مصارعة)"
_BLOCKLIST_EN = r"(MMA|Boxing|Karate|Judo|Taekwondo|Soccer|Football|Basketball|Tennis|Swim|Swimming|Running|Run|Cycle|Cycling|Bike|Biking|Yoga|Pilates|Rowing|Row|Skate|Skating|Ski|Skiing|Climb|Climbing|Surf|Surfing|Golf|Volleyball|Handball|Hockey|Parkour|Wrestling)"
_name_re = re.compile(_BLOCKLIST_AR + "|" + _BLOCKLIST_EN, re.IGNORECASE)

_AVOID_GENERIC = [
    "أي نشاط بدني مفيد","اختر ما يناسبك","ابدأ بأي شيء","جرّب أكثر من خيار",
    "لا يهم النوع","تحرك فقط","نشاط عام","رياضة عامة","أنت تعرف ما يناسبك"
]
_SENSORY = [
    "تنفّس","إيقاع","توتر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","امتداد","حرق لطيف","صفاء","تماسك"
]
_GENERIC_LABEL_RE = re.compile(
    r"(impress\w*\s+compact|generic\s+(sport|identity)|basic\s+flow|simple\s+flow|body\s+flow)",
    re.IGNORECASE
)

def _split_sentences(text: str) -> List[str]:
    if not text: return []
    return [s.strip() for s in re.split(r'(?<=[.!؟])\s+|[\n،]+', text) if s.strip()]

_FORBIDDEN_SENT = re.compile(
    r"(\b\d+(\.\d+)?\s*(?:min|mins|minute|minutes|second|seconds|hour|hours|دقيقة|دقائق|ثانية|ثواني|ساعة|ساعات)\b|"
    r"(?:rep|reps|set|sets|تكرار|عدة|عدات|جولة|جولات|×)|"
    r"(?:تكلفة|ميزانية|cost|budget|ريال|دولار|\$|€)|"
    r"(?:بالبيت|في\s*البيت|قرب\s*المنزل|بالمنزل|في\s*النادي|في\s*الجيم|صالة|نادي|جيم|غرفة|ساحة|ملعب|حديقة|شاطئ|"
    r"طبيعة|خارجي(?:ة)?|داخل(?:ي|ية)?|outdoor|indoor|park|beach|gym|studio))",
    re.IGNORECASE
)

def _contains_blocked_name(t: str) -> bool:
    if not t: return False
    return bool(_name_re.search(t)) or bool(_name_re.search(_normalize_ar(t)))

def _mask_names(t: str) -> str:
    if ALLOW_SPORT_NAMES:
        return t or ""
    s = t or ""
    s = _name_re.sub("—", s)
    if s == (t or "") and _contains_blocked_name(t):
        s = "—"
    return s

def _scrub_forbidden(text: str) -> str:
    if not text: return ""
    kept = [s for s in _split_sentences(text) if not _FORBIDDEN_SENT.search(_normalize_ar(s))]
    out = "، ".join(kept).strip(" .،")
    if not out:
        out = _FORBIDDEN_SENT.sub("", _normalize_ar(text))
        out = re.sub(r"\s{2,}", " ", out).strip(" .،")
        if not out:
            out = text
    return out

def _clip(s: str, n: int) -> str:
    if not s: return ""
    s = s.strip()
    return s if len(s) <= n else (s[: max(0, n - 1)] + "…")

def _to_bullets(text_or_list: Any, max_items: int = 6) -> List[str]:
    out: List[str] = []
    def _flat_add(x: Any) -> None:
        if x is None: return
        if isinstance(x, (list, tuple, set)):
            for y in x: _flat_add(y)
            return
        if isinstance(x, dict):
            for k in ("text", "desc", "value", "answer", "label", "title"):
                if k in x and isinstance(x[k], str) and x[k].strip():
                    out.append(x[k].strip()); return
            out.append(json.dumps(x, ensure_ascii=False)); return
        s = _norm_text(x).strip()
        if s: out.append(s)
    _flat_add(text_or_list)
    if len(out) == 1 and isinstance(text_or_list, str):
        raw = re.split(r"[;\n\.،]+", out[0])
        out = [i.strip(" -•\t ") for i in raw if i.strip()]
    out = out[:max_items]
    out = [str(i) for i in out if str(i).strip()]
    return out

# ========= Z-axes alignment =========
_AR_TOK = {
    "calm": ["هدوء","تنفّس","بطيء","استرخاء","صفاء","سكون"],
    "adren": ["اندفاع","كمين","سريع","انقضاض","إثارة","قرار خاطف"],
    "solo": ["فردي","لوحدك","ذاتية"],
    "group": ["جماعة","شريك","فريق","تعاون"],
    "tech": ["تقنية","تفاصيل","صقل","دقة","ضبط"],
    "intu": ["على الإحساس","حدس","تلقائية","تدفّق"]
}
_EN_TOK = {
    "calm": ["calm","breath","slow","relax","settle"],
    "adren": ["burst","fast","risk","strike","adrenaline"],
    "solo": ["solo","alone","individual"],
    "group": ["team","partner","group","co-op"],
    "tech": ["technique","detail","precision","drill","refine"],
    "intu": ["by feel","intuitive","flow","improvise"]
}
def _axes_expectations(axes: Dict[str, float], lang: str) -> Dict[str, List[str]]:
    tok = _AR_TOK if lang == "العربية" else _EN_TOK
    out: Dict[str, List[str]] = {}
    if not isinstance(axes, dict): return out
    ca = axes.get("calm_adrenaline")
    if isinstance(ca, (int, float)):
        out["calm_adrenaline"] = tok["adren"] if ca >= 0.5 else tok["calm"] if ca <= -0.5 else []
    sg = axes.get("solo_group")
    if isinstance(sg, (int, float)):
        out["solo_group"] = tok["group"] if sg >= 0.5 else tok["solo"] if sg <= -0.5 else []
    ti = axes.get("tech_intuition")
    if isinstance(ti, (int, float)):
        out["tech_intuition"] = tok["intu"] if ti >= 0.5 else tok["tech"] if ti <= -0.5 else []
    return out

def _mismatch_with_axes(rec: Dict[str, Any], axes: Dict[str, float], lang: str) -> bool:
    exp = _axes_expectations(axes or {}, lang)
    if not exp: return False
    blob = " ".join(_norm_text(rec.get(k,"")) for k in ("what_it_looks_like","inner_sensation","why_you","first_week"))
    blob_l = blob.lower()
    for _, words in exp.items():
        if words and not any(w.lower() in blob_l for w in words):
            return True
    return False

# ========= Label normalization / similarity =========
def _canonical_label(label: str) -> str:
    if not label: return ""
    lab = re.sub(r"\s+", " ", label).strip(" -—:،").lower()
    lab = _normalize_ar(lab)
    return lab

def _label_is_generic(label: str) -> bool:
    # نتحقق من النسخة الـcanonical ومن أي تطابق مع الريجيكس المرن
    if not label:
        return True
    lab = _canonical_label(label)
    if (lab in _GENERIC_LABELS) or (len(lab) <= 3):
        return True
    return bool(_GENERIC_LABEL_RE.search(label))

def _tokenize(text: str) -> List[str]:
    if not text: return []
    t = _normalize_ar(text.lower())
    toks = re.split(r"[^a-zA-Z0-9\u0600-\u06FF]+", t)
    return [w for w in toks if w and len(w) > 2]

def _sig_for_rec(r: Dict[str, Any]) -> set:
    core = r.get("core_skills") or []
    core_txt = " ".join(core) if isinstance(core, list) else str(core)
    toks = set(_tokenize(r.get("sport_label","")) + _tokenize(core_txt))
    return toks

def _jaccard(a: set, b: set) -> float:
    if not a and not b: return 1.0
    inter = len(a & b)
    union = len(a | b) or 1
    return inter / union

# ========= Sanitizers / Fallbacks =========
def _sanitize_record(r: Dict[str, Any]) -> Dict[str, Any]:
    r = dict(r or {})
    r.pop("practical_fit", None)
    for k in ("sport_label","scene","what_it_looks_like","inner_sensation","why_you",
              "first_week","progress_markers","win_condition","variant_vr","variant_no_vr","vr_idea","mode"):
        if k in r:
            s = _scrub_forbidden(_mask_names(_norm_text(r.get(k))))
            r[k] = s
    cs = r.get("core_skills")
    if isinstance(cs, str):
        parts = [p.strip(" -•\t") for p in re.split(r"[,\n،]+", cs) if p.strip()]
        r["core_skills"] = parts[:6]
    elif isinstance(cs, (list, tuple)):
        skills = [_norm_text(x).strip() for x in cs if _norm_text(x).strip()]
        r["core_skills"] = skills[:6]
    else:
        r["core_skills"] = []
    try:
        d = int(r.get("difficulty", 3))
        r["difficulty"] = max(1, min(5, d))
    except Exception:
        r["difficulty"] = 3
    if r.get("mode") not in ("Solo","Team","Solo/Team","فردي","جماعي","فردي/جماعي"):
        r["mode"] = r.get("mode","Solo")
    return r

# ========= Fallback identities (AR/EN) =========
def _fallback_identity(i: int, lang: str) -> Dict[str, Any]:
    if lang == "العربية":
        presets = [
            {
                "sport_label":"Tactical Immersive Combat",
                "what_it_looks_like":"ساحة محاكاة بصرية أو VR: تتبّع، كمين، قرار خاطف، اقتراب محسوب، انسحاب آمن.",
                "inner_sensation":"اندماج ذهني مع يقظة عالية وثقة هادئة.",
                "why_you":"تكره التكرار وتفضّل صراعًا تكتيكيًا يختبر الذكاء والأعصاب.",
                "first_week":"ابدأ بجولة حسّية: تعرّف على الإيقاع، جرّب اقتراب/انسحاب، وثبّت تنفّسك قبل القرار.",
                "progress_markers":"قرارات أسرع، هدوء تحت الضغط، إحساس بسيطرة أعلى.",
                "win_condition":"الوصول لهدف دون انكشاف أو تعطيل 'الخصم' بقرار خاطف.",
                "core_skills":["تتبّع زاوية الرؤية","تغيير الإيقاع","قرار سريع","ثبات التوازن","تنفّس هادئ"],
                "mode":"Solo/Team",
                "variant_vr":"مبارزات تكتيكية في VR مع تتبع مجال رؤية الخصم.",
                "variant_no_vr":"عقبات خفيفة مع ممرات ظلّ.",
                "difficulty":3
            },
            {
                "sport_label":"Stealth-Flow Missions",
                "what_it_looks_like":"مسار صامت متدرّج: اختباء قصير، ظهور محسوب، لمس 'علامة' ثم اختفاء.",
                "inner_sensation":"تركيز عميق وتنظيم للنفس مع حركة ناعمة.",
                "why_you":"تبغى تقدّم ملموس بدون ضجيج وتحب الإتقان الهادئ.",
                "first_week":"درّب تبديل السرعات بسلاسة وملاحظة الزوايا الآمنة.",
                "progress_markers":"توتر أقل، نعومة حركة، قرارات أوضح.",
                "win_condition":"إنجاز المهمة دون انكشاف.",
                "core_skills":["توقيت الظهور","قراءة الحواجز","تعديل الإيقاع","تنفّس صامت","توازن"],
                "mode":"Solo",
                "variant_vr":"تسلل افتراضي مع مؤشّر انكشاف بصري.",
                "variant_no_vr":"عوائق خفيفة وأشرطة ظل.",
                "difficulty":2
            },
            {
                "sport_label":"Mind-Trap Puzzles in Motion",
                "what_it_looks_like":"ألغاز قرار أثناء الحركة: تحويل مسار، خدعة بصرية، حركة مضادة لحركة 'خصم' افتراضي.",
                "inner_sensation":"فضول ذهني مع لذّة الاكتشاف.",
                "why_you":"تحب الفهم العميق ومبارزة الهوية ذهنيًا قبل جسديًا.",
                "first_week":"حل لغز حركي بسيط مع تتبّع النفس، ثم أضف خدعة واحدة.",
                "progress_markers":"وضوح تركيز، ثقة قرار، تناغم حركة/فكر.",
                "win_condition":"حل اللغز دون أخطاء متتالية.",
                "core_skills":["خداع بصري","تحويل مسار","تثبيت نظرة","قرار بديهي","هدوء تحت ضغط"],
                "mode":"Solo",
                "variant_vr":"أفخاخ بصرية تفاعلية.",
                "variant_no_vr":"مسارات أرضية ذات إشارات مخفية.",
                "difficulty":2
            },
            {
                "sport_label":"Range Precision Circuit",
                "what_it_looks_like":"دقة تصويب هادئة مع زوايا ثابتة وانتقال منظّم بين أهداف.",
                "inner_sensation":"هدوء متمركز ونبض مستقر.",
                "why_you":"تميل لتهذيب التقنية والاتقان الصامت.",
                "first_week":"ثبّت النظرة، اضبط النفس، بدّل زواياك بسلاسة.",
                "progress_markers":"ثبات يد، قرار أوضح، توتر أقل.",
                "win_condition":"تحقيق دقة ثابتة عبر سلسلة أهداف دون أخطاء متتالية.",
                "core_skills":["تثبيت نظرة","ضبط نفس","انتقال زوايا","تحكّم دقيق"],
                "mode":"Solo",
                "variant_vr":"تصويب افتراضي تفاعلي.",
                "variant_no_vr":"لوحات أهداف إسفنجية آمنة.",
                "difficulty":2
            },
            {
                "sport_label":"Grip & Balance Ascent",
                "what_it_looks_like":"مسار قبضات وتوازن تدريجي، قراءة مسك، تحويل وزن هادئ.",
                "inner_sensation":"تماسك داخلي وثقة حركة.",
                "why_you":"تحب تحدّي تحكّم الجسد بدون ضجيج.",
                "first_week":"اقرأ موضع القبضة، وزّن الحمل، تحرّك ببطء صاعد.",
                "progress_markers":"تعب أقل في الساعد، اتزان أوضح.",
                "win_condition":"الوصول للنقطة العلوية دون إفلات.",
                "core_skills":["قبضة","تحويل وزن","توازن","قراءة مسار"],
                "mode":"Solo",
                "variant_vr":"مسارات قبضات افتراضية.",
                "variant_no_vr":"عناصر قبضة آمنة خفيفة.",
                "difficulty":2
            }
        ]
    else:
        presets = [
            {
                "sport_label":"Tactical Immersive Combat",
                "what_it_looks_like":"Arena/VR with tracking, ambush, snap decisions, calculated approach and safe exit.",
                "inner_sensation":"Locked-in focus with calm confidence.",
                "why_you":"You dislike repetition and enjoy tactical mind-body duels.",
                "first_week":"Feel the rhythm, practice approach/retreat, anchor breath before decisions.",
                "progress_markers":"Faster decisions, calmer under pressure, stronger control.",
                "win_condition":"Reach objective unseen or neutralize threat via snap decision.",
                "core_skills":["angle tracking","tempo shifts","fast decision","balance","quiet breath"],
                "mode":"Solo/Team",
                "variant_vr":"Tactical VR duels with FOV tracking.",
                "variant_no_vr":"Foam obstacles with shadow lanes.",
                "difficulty":3
            },
            {
                "sport_label":"Stealth-Flow Missions",
                "what_it_looks_like":"Silent path: brief hide, measured reveal, tag and vanish.",
                "inner_sensation":"Deep focus with smooth breathing.",
                "why_you":"You want tangible progress without noise and love quiet mastery.",
                "first_week":"Practice smooth tempo shifts and safe angles.",
                "progress_markers":"Lower tension, smoother movement, clearer decisions.",
                "win_condition":"Complete the mission without detection.",
                "core_skills":["timed reveal","reading cover","tempo control","silent breath","balance"],
                "mode":"Solo",
                "variant_vr":"Stealth VR with exposure indicator.",
                "variant_no_vr":"Light obstacles and shadow tapes.",
                "difficulty":2
            },
            {
                "sport_label":"Mind-Trap Puzzles in Motion",
                "what_it_looks_like":"Decision puzzles in motion: route switch, visual feint, counter-move.",
                "inner_sensation":"Curious mind with discovery joy.",
                "why_you":"You enjoy deep understanding and identity duels—mind first.",
                "first_week":"Solve a simple motion puzzle with breath tracking; add one feint.",
                "progress_markers":"Sharper focus, steadier decisions, mind–body sync.",
                "win_condition":"Solve without consecutive errors.",
                "core_skills":["visual feint","path switch","gaze hold","intuitive decision","calm under stress"],
                "mode":"Solo",
                "variant_vr":"Interactive visual traps.",
                "variant_no_vr":"Floor cues with hidden hints.",
                "difficulty":2
            }
        ]
    return presets[i % len(presets)]

def _fill_defaults(r: Dict[str, Any], lang: str) -> Dict[str, Any]:
    r = dict(r or {})
    if not r.get("win_condition"):
        r["win_condition"] = ("إنجاز المهمة دون انكشاف." if lang=="العربية"
                              else "Complete the mission without being detected.")
    if not r.get("core_skills"):
        r["core_skills"] = ["تتبّع زاوية الرؤية","تغيير الإيقاع","قرار سريع"] if lang=="العربية" \
                           else ["angle tracking","tempo shifts","fast decision"]
    if not r.get("mode"):
        r["mode"] = "Solo/Team"
    if not r.get("variant_vr"):
        r["variant_vr"] = ("مبارزات تكتيكية في VR مع مؤشّر مجال رؤية." if lang=="العربية"
                           else "Tactical VR duels with FOV indicator.")
    if not r.get("variant_no_vr"):
        r["variant_no_vr"] = ("عقبات خفيفة مع ممرات ظل." if lang=="العربية"
                              else "Light obstacle arena with shadow lanes.")
    return r

# ======== HARD DEDUPE (no repeats, no near-duplicates) ========
def _hard_dedupe_and_fill(recs: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    used_labels = set()
    used_sigs: List[set] = []

    def pick_unique_fallback(idx: int) -> Dict[str, Any]:
        for j in range(idx, idx+6):
            fb = _fallback_identity(j, lang)
            lab = _canonical_label(fb.get("sport_label",""))
            sig = _sig_for_rec(fb)
            if lab and (lab not in used_labels) and all(_jaccard(sig, s) <= 0.6 for s in used_sigs):
                return fb
        fb = _fallback_identity(idx, lang)
        fb["sport_label"] = (fb.get("sport_label","") + " — Alt")
        return fb

    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        r = _fill_defaults(_sanitize_record(r), lang)

        lab = _canonical_label(r.get("sport_label",""))
        if not lab or _label_is_generic(lab):
            r = pick_unique_fallback(i); lab = _canonical_label(r.get("sport_label",""))

        if lab in used_labels:
            r = pick_unique_fallback(i); lab = _canonical_label(r.get("sport_label",""))

        sig = _sig_for_rec(r)
        if any(_jaccard(sig, s) > 0.6 for s in used_sigs):
            r = pick_unique_fallback(i); lab = _canonical_label(r.get("sport_label","")); sig = _sig_for_rec(r)

        out.append(r)
        used_labels.add(lab)
        used_sigs.append(sig)

    return out

# ========= Traits & Scoring =========
def _derive_binary_traits(analysis: Dict[str, Any], answers: Dict[str, Any], lang: str) -> Dict[str, float]:
    traits: Dict[str, float] = {}
    prof = (analysis or {}).get("encoded_profile") or {}
    axes = (prof or {}).get("axes") or {}
    silent = set(map(str, (analysis or {}).get("silent_drivers") or []))
    sig = _extract_signals(answers, lang)

    sg = float(axes.get("solo_group", 0.0)) if isinstance(axes, dict) else 0.0
    if sg <= -0.35: traits["introvert"] = 1.0; traits["prefers_solo"] = 1.0
    if sg >=  0.35: traits["extrovert"] = 1.0; traits["prefers_team"] = 1.0
    if sig.get("solo_pref"): traits["prefers_solo"] = max(1.0, traits.get("prefers_solo", 0))
    if sig.get("team_pref"): traits["prefers_team"] = max(1.0, traits.get("prefers_team", 0))

    ca = float(axes.get("calm_adrenaline", 0.0)) if isinstance(axes, dict) else 0.0
    if ca <= -0.35 or sig.get("breath"):
        traits["calm_regulation"] = max(traits.get("calm_regulation", 0.0), 0.8)
    if ca >= 0.35 or sig.get("high_agg"):
        traits["sensation_seeking"] = max(traits.get("sensation_seeking", 0.0), 0.8)

    ti_val = axes.get("tech_intuition", 0.0)
    ti = float(ti_val) if isinstance(ti_val, (int, float)) else 0.0
    if ti <= -0.35 or sig.get("precision"):
        traits["precision"] = max(traits.get("precision", 0.0), 0.8)

    if sig.get("stealth"):
        traits["tactical_mindset"] = max(1.0, traits.get("tactical_mindset", 0))
    if sig.get("puzzles"): traits["likes_puzzles"] = 1.0
    if sig.get("combat"): traits["tactical_mindset"] = max(1.0, traits.get("tactical_mindset", 0))
    vr_i = float((prof or {}).get("vr_inclination", 0.0))
    if sig.get("vr") or vr_i >= 0.4:
        traits["vr_inclination"] = max(traits.get("vr_inclination", 0.0), max(vr_i, 0.8))

    if traits.get("calm_regulation", 0) >= 0.8 or traits.get("likes_puzzles", 0) >= 1.0:
        traits["sustained_attention"] = max(traits.get("sustained_attention", 0.0), 0.6)

    ar_blob = _normalize_ar(" ".join(_norm_answer_value(v) for v in (answers or {}).values()).lower())
    if any(w in ar_blob for w in ["قلق","مخاوف","توتر شديد","رهاب","خوف"]):
        traits["anxious"] = 1.0
    if any("نفور" in s or "تكرار" in s for s in silent):
        traits["low_repetition_tolerance"] = 1.0
    if any("انجازات قصيره" in _normalize_ar(s) for s in silent):
        traits["needs_quick_wins"] = 1.0

    return traits

def _score_candidates_from_links(traits: Dict[str, float]) -> List[Tuple[float, str]]:
    anxious = traits.get("anxious", 0.0) >= 0.8 and GUARDS.get("no_high_risk_for_anxiety", True)
    labels = set(KB_PRIORS.keys())
    for t, mapping in (TRAIT_LINKS or {}).items():
        labels.update(mapping.keys())
    scored: List[Tuple[float, str]] = []
    for label in labels:
        if anxious and label in HIGH_RISK_SPORTS:
            scored.append((-1e9, label)); continue
        s = float(KB_PRIORS.get(label, 0.0))
        for t_name, strength in traits.items():
            link = (TRAIT_LINKS.get(t_name) or {}).get(label, 0.0)
            if link: s += float(strength) * float(link)
        scored.append((s, label))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

# ========= Templates by label (AR/EN) =========
def _canon_label(label: str) -> str:
    lab = _normalize_ar((label or "")).lower().strip(" -—:،")
    if not lab: return ""
    if lab in _ALIAS_MAP: return _ALIAS_MAP[lab]
    lab = re.sub(r"[^a-z0-9\u0600-\u06FF]+", " ", lab)
    lab = re.sub(r"\s+", " ", lab).strip()
    return lab

def _is_forbidden_generic(label: str) -> bool:
    base = _normalize_ar((label or "")).lower()
    return any(g in base for g in _FORBIDDEN_GENERIC)

def _template_for_label(label: str, lang: str) -> Optional[Dict[str, Any]]:
    L = _canon_label(label)
    KB_PRESETS = {
        "tactical_immersive_combat": _fallback_identity(0, lang),
        "stealth_flow_missions": _fallback_identity(1, lang),
        "mind_trap_puzzles": _fallback_identity(2, lang),
        "range_precision_circuit": _fallback_identity(3, lang),
        "grip_balance_ascent": _fallback_identity(4, lang),
    }
    if L in KB_PRESETS:
        return _sanitize_record(_fill_defaults(KB_PRESETS[L], lang))
    return None

# ====== Blacklist (persistent, JSON) =========================================
def _load_blacklist() -> dict:
    if FILELOCK_OK:
        try:
            with FileLock(str(BL_PATH) + ".lock", timeout=3):
                bl = _load_json_safe(BL_PATH)
        except Timeout:
            _warn("blacklist lock timeout on read; proceeding without lock")
            bl = _load_json_safe(BL_PATH)
    else:
        time.sleep(0.01 + random.random()*0.02)
        bl = _load_json_safe(BL_PATH)

    if not isinstance(bl.get("labels"), dict):
        bl["labels"] = {}
    bl.setdefault("version", "1.0")
    return bl

def _bl_has(bl: dict, label: str) -> bool:
    c = _canon_label(label)
    return bool(c and c in bl["labels"])

def _bl_add(bl: dict, label: str, alias: str = "") -> None:
    c = _canon_label(label)
    if not c: return
    rec = bl["labels"].get(c, {"aliases": [], "count": 0, "first_seen": None})
    if alias and alias not in rec["aliases"]:
        rec["aliases"].append(alias)
    rec["count"] = int(rec.get("count", 0)) + 1
    if not rec.get("first_seen"):
        rec["first_seen"] = datetime.utcnow().isoformat() + "Z"
    rec["last_used"] = datetime.utcnow().isoformat() + "Z"
    bl["labels"][c] = rec

_AR_VARIANTS = [
    "نسخة ظلّية","نمط مراوغة","خط تحكّم هادئ","نسخة تفكيك تكتيكي",
    "مناورة عكسية","زاوية صامتة","طيف التتبع","تدفق خفي","إزاحة مقصودة",
]
_EN_VARIANTS = [
    "Shadow Variant","Evasive Pattern","Calm-Control Line","Tactical Deconstruction",
    "Counter-Maneuver","Silent Angle","Tracking Flux","Stealth Flow","Angle Shift",
]

def _generate_variant_label(base: str, lang: str, salt: int = 0) -> str:
    base = (base or "").strip(" -—:،")
    pool = _AR_VARIANTS if lang == "العربية" else _EN_VARIANTS
    joiner = " — "
    idx = abs(hash(_normalize_ar(base) + str(salt))) % len(pool)
    return f"{base}{joiner}{pool[idx]}"

def _perturb_phrasing(rec: Dict[str, Any], lang: str) -> Dict[str, Any]:
    r = dict(rec)
    tacky_add_ar = " ركّز على قراءة الزوايا بدل مطاردة الحركة. اجعل القرار يظهر فجأة عندما يهدأ الإيقاع."
    tacky_add_en = " Emphasize reading angles over chasing motion; let decisions snap when the rhythm calms."
    if lang == "العربية":
        r["what_it_looks_like"] = (r.get("what_it_looks_like","") + tacky_add_ar).strip()
        r["why_you"] = (r.get("why_you","") + " تحب الاختصار الذكي وإخفاء نواياك حتى اللحظة المناسبة.").strip()
    else:
        r["what_it_looks_like"] = (r.get("what_it_looks_like","") + tacky_add_en).strip()
        r["why_you"] = (r.get("why_you","") + " You like smart brevity and hiding intent until the decisive beat.").strip()
    return r

def _ensure_unique_labels_v_global(recs: List[Dict[str, Any]], lang: str, bl: dict) -> List[Dict[str, Any]]:
    used_now = set()
    out = []
    for r in recs:
        r = dict(r or {})
        label = r.get("sport_label") or ""
        if _is_forbidden_generic(label) or not label.strip():
            label = "تكتيكي تخفّي" if lang == "العربية" else "Tactical Stealth"
            r["sport_label"] = label
        salt = 0
        while _bl_has(bl, label) or _canon_label(label) in used_now:
            label = _generate_variant_label(label, lang, salt=salt)
            r = _perturb_phrasing(r, lang)
            salt += 1
        used_now.add(_canon_label(label))
        r["sport_label"] = label
        out.append(r)
    return out

def _persist_blacklist(recs: List[Dict[str, Any]], bl: dict) -> None:
    def _write():
        for r in recs:
            lab = r.get("sport_label") or ""
            if lab.strip():
                _bl_add(bl, lab, alias=lab)
        _save_json_atomic(BL_PATH, bl)

    if FILELOCK_OK:
        try:
            with FileLock(str(BL_PATH) + ".lock", timeout=4):
                _write()
        except Timeout:
            _warn("blacklist lock timeout on write; writing without lock")
            _write()
    else:
        time.sleep(0.01 + random.random()*0.03)
        _write()

# ========= Prompt Builder / JSON parsing =========
def _style_seed(user_id: str, profile: Optional[Dict[str, Any]]) -> int:
    base = user_id or "anon"
    axes = profile.get("axes", {}) if isinstance(profile, dict) else {}
    s = f"{base}:{json.dumps(axes, sort_keys=True, ensure_ascii=False)}"
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _answers_to_bullets(answers: Dict[str, Any]) -> str:
    lines: List[str] = []
    for k, v in (answers or {}).items():
        lines.append(f"- {k}: {_norm_answer_value(v)}")
    text = "\n".join(lines)
    if len(text) > MAX_PROMPT_CHARS//2:
        text = text[:MAX_PROMPT_CHARS//2] + "\n- …"
    return text

def _strip_code_fence(s: str) -> str:
    if not s: return s
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s

def _parse_llm_json(txt: str) -> Optional[dict]:
    if not txt: return None
    raw = _strip_code_fence(txt)
    try:
        return json.loads(raw)
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        frag = m.group(0)
        try:
            return json.loads(frag)
        except Exception:
            if REC_REPAIR_ENABLED:
                frag2 = re.sub(r",(\s*[}\]])", r"\1", frag)
                try:
                    return json.loads(frag2)
                except Exception:
                    return None
    return None

def _too_generic(text: str, min_chars: int) -> bool:
    t = _normalize_ar(text or "")
    if len(t) < min_chars: return True
    return any(p in t for p in [_normalize_ar(x) for x in _AVOID_GENERIC])

def _has_sensory(text: str) -> bool:
    t = _normalize_ar(text or "")
    return any(_normalize_ar(s) in t for s in _SENSORY)

def _is_meaningful(rec: Dict[str, Any]) -> bool:
    lab = _norm_text(rec.get("sport_label","")).strip()
    looks = _norm_text(rec.get("what_it_looks_like","")).strip()
    return bool(lab and looks and len(_normalize_ar(looks)) >= 30)

def _compact_analysis_for_prompt(analysis: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    p_axes   = (profile or {}).get("axes", {})
    p_signals= (profile or {}).get("signals", [])
    hints    = (profile or {}).get("hints_for_prompt", "")
    out = {
        "silent_drivers": analysis.get("silent_drivers", []),
        "z_axes": analysis.get("z_axes", p_axes),
        "z_intent": analysis.get("z_intent", []),
        "encoded_profile": {"axes": p_axes, "signals": p_signals, "hints": _clip(str(hints), 300)},
    }
    blob = json.dumps(out, ensure_ascii=False)
    if len(blob) > MAX_PROMPT_CHARS // 2:
        out["encoded_profile"]["signals"] = out["encoded_profile"]["signals"][:10]
    return out

# ========= Core: KB-first then LLM fallback =========
def _kb_candidates(analysis: Dict[str, Any], answers: Dict[str, Any], lang: str) -> List[Dict[str, Any]]:
    profile = (analysis or {}).get("encoded_profile") or {}
    axes = (profile or {}).get("axes") or {}
    signals = _extract_signals(answers, lang)
    ids = KB.get("identities") or []
    ranked_from_kb: List[Dict[str, Any]] = []
    if ids:
        exp = _axes_expectations(axes or {}, lang)
        scored: List[Tuple[int, Dict[str, Any]]] = []
        for rec in ids:
            r = _sanitize_record(rec)
            blob = " ".join([_norm_text(r.get("what_it_looks_like","")),
                             _norm_text(r.get("why_you","")),
                             _norm_text(r.get("first_week",""))]).lower()
            hit = 0
            for words in exp.values():
                if words and any(w.lower() in blob for w in words): hit += 1
            if signals.get("precision") and ("precision" in blob or "دقه" in blob): hit += 1
            if signals.get("stealth") and ("stealth" in blob or "تخفي" in blob): hit += 1
            scored.append((hit, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        ranked_from_kb = [s[1] for s in scored[:3]]
    return ranked_from_kb

def _llm_fallback(user_id: str, analysis: Dict[str, Any], answers: Dict[str, Any], lang: str) -> List[Dict[str, Any]]:
    if not LLM_CLIENT:
        return []
    profile = analysis.get("encoded_profile") or {}
    bullets = _answers_to_bullets(answers)
    compact = _compact_analysis_for_prompt(analysis, profile)

    sys_ar = (
        "أنت نظام توصيات رياضية. أعد JSON فقط بدون أي نص خارج JSON. امنع ذكر الوقت/التكلفة/المكان/العدات."
        " يجب أن تُرجع 3 عناصر تحت المفتاح 'cards'، كل عنصر يحوي: "
        "sport_label, what_it_looks_like, inner_sensation, why_you, first_week, progress_markers, win_condition, core_skills (list<=6), mode, variant_vr, variant_no_vr, difficulty(1-5)."
    )
    sys_en = (
        "You are a sport-identity recommender. Return JSON ONLY, no prose. Forbid time/cost/location/equipment mentions."
        " Return exactly 3 items under 'cards' with keys: "
        "sport_label, what_it_looks_like, inner_sensation, why_you, first_week, progress_markers, win_condition, core_skills (list<=6), mode, variant_vr, variant_no_vr, difficulty(1-5)."
    )
    system = sys_ar if lang=="العربية" else sys_en
    user_blob = {
        "lang": lang,
        "answers_bullets": bullets,
        "profile_compact": compact,
        "constraints": {
            "no_time_cost_place_sets": True,
            "min_chars_each": _MIN_CHARS,
            "require_win": _REQUIRE_WIN,
            "min_core_skills": _MIN_CORE_SKILLS
        }
    }

    msgs = [
        {"role":"system","content":system},
        {"role":"user","content":json.dumps(user_blob, ensure_ascii=False)}
    ]
    temp_primary = 0.6 if not REC_FAST_MODE else 0.5
    temp_repair  = 0.35

    t0 = time.perf_counter()
    out_txt = ""
    try:
        out_txt = chat_once(
            client=LLM_CLIENT,
            model=CHAT_MODEL,
            messages=msgs,
            temperature=temp_primary,
            timeout_s=min(REC_BUDGET_S, 18.0),
        )
    except Exception as e:
        _warn(f"chat_once primary failed: {e}")
        try:
            out_txt = chat_once(
                client=LLM_CLIENT,
                model=CHAT_MODEL_FALLBACK or CHAT_MODEL,
                messages=msgs,
                temperature=temp_primary,
                timeout_s=min(REC_BUDGET_S, 18.0),
            )
        except Exception as e2:
            _err(f"chat_once fallback failed: {e2}")
            return []

    data = _parse_llm_json(out_txt or "")
    if not data and REC_REPAIR_ENABLED:
        _dbg("repair: forcing JSON only")
        msgs2 = [
            {"role":"system","content":system},
            {"role":"user","content":"أعد نفس الإجابة بصيغة JSON فقط بدون أي نص خارج JSON." if lang=="العربية"
             else "Return the same answer as pure JSON only, with no prose outside JSON."}
        ]
        try:
            out_txt2 = chat_once(
                client=LLM_CLIENT,
                model=CHAT_MODEL_FALLBACK or CHAT_MODEL,
                messages=msgs + msgs2,
                temperature=temp_repair,
                timeout_s=max(4.0, min(REC_BUDGET_S - (time.perf_counter()-t0), 8.0)),
            )
            data = _parse_llm_json(out_txt2 or "")
        except Exception as e:
            _warn(f"repair round failed: {e}")
            data = None

    cards: List[Dict[str, Any]] = []
    if isinstance(data, dict) and isinstance(data.get("cards"), list):
        for item in data["cards"][:3]:
            if isinstance(item, dict):
                cards.append(_sanitize_record(item))
    return cards

# ========= Global ensure / rendering =========
def _fill_defaults_batch(cards: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    return [_fill_defaults(c, lang) for c in cards]

def _quality_filter(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for c in cards:
        if not _is_meaningful(c): 
            continue
        if _too_generic(c.get("what_it_looks_like",""), _MIN_CHARS):
            continue
        if _REQUIRE_WIN and not (c.get("win_condition") or "").strip():
            continue
        if len(c.get("core_skills") or []) < _MIN_CORE_SKILLS:
            continue
        # لتشديد الحسّ الجسدي فعّل:
        # if not _has_sensory((c.get("inner_sensation","") + " " + c.get("what_it_looks_like","")).strip()):
        #     continue
        out.append(c)
    return out

def _brand_footer(lang: str) -> str:
    return "— Sports Sync" if lang != "العربية" else "— Sports Sync"

def _format_card(c: Dict[str, Any], lang: str) -> str:
    lines: List[str] = []
    lines.append(f"### {c.get('sport_label','')}")
    if c.get('what_it_looks_like'):
        lines.append(f"{c['what_it_looks_like']}")
    if c.get('inner_sensation'):
        lines.append(f"• الإحساس الداخلي: {c['inner_sensation']}" if lang=="العربية" else f"• Inner feel: {c['inner_sensation']}")
    if c.get('why_you'):
        lines.append(f"• لماذا أنت: {c['why_you']}" if lang=="العربية" else f"• Why you: {c['why_you']}")
    if c.get('first_week'):
        lines.append(f"• أول أسبوع: {c['first_week']}" if lang=="العربية" else f"• First week: {c['first_week']}")

    pm = c.get('progress_markers')
    if isinstance(pm, (list, tuple, set)):
        pm_list = _to_bullets(pm, 6)
        if pm_list:
            lines.append(("• مؤشرات التقدم: " if lang=="العربية" else "• Progress markers: ")
                         + "، ".join(map(str, pm_list)))
    elif pm:
        lines.append(f"• مؤشرات التقدم: {pm}" if lang=="العربية" else f"• Progress markers: {pm}")

    if c.get('win_condition'):
        lines.append(f"• شرط الفوز/الهدف: {c['win_condition']}" if lang=="العربية" else f"• Win condition: {c['win_condition']}")

    skills = _to_bullets(c.get('core_skills', []), 6)
    if skills:
        lines.append(("• مهارات أساسية: " if lang=="العربية" else "• Core skills: ")
                     + "، ".join(map(str, skills)))

    if c.get('mode'):
        lines.append(("• النمط: " if lang=="العربية" else "• Mode: ") + str(c['mode']))
    if c.get('variant_vr'):
        lines.append(("• نسخة VR: " if lang=="العربية" else "• VR variant: ") + str(c['variant_vr']))
    if c.get('variant_no_vr'):
        lines.append(("• نسخة بلا VR: " if lang=="العربية" else "• No-VR variant: ") + str(c['variant_no_vr']))

    lines.append(_brand_footer(lang))
    return "\n".join(map(str, lines)).strip()

# ========= Public API =========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
    """
    واجهة موحّدة لـ app.py: ترجع 3 بطاقات نصّية (List[str]).
    - Evidence Gate → followups إن لزم
    - KB-first
    - LLM fallback (إن توفر مفتاح)
    - Sanitize + dedupe + blacklist global uniqueness
    """
    t0 = time.perf_counter()
    timings: Dict[str, int] = {}

    # 0) Evidence Gate
    eg_t0 = time.perf_counter()
    eg = _run_egate(answers, lang=lang)
    timings["egate_ms"] = int((time.perf_counter() - eg_t0) * 1000)
    if eg.get("status") != "pass":
        follow = _format_followup_card(eg.get("followup_questions", [])[:3], lang)
        _dbg(f"egate: {timings['egate_ms']}ms | blocked (need followups)")
        return [follow, "—", "—"]

    user_id = "web_user"

    # 0.1) Analysis (silent drivers + encoded profile + intent)
    ana_t0 = time.perf_counter()
    analysis = {
        "encoded_profile": _extract_profile(answers, lang) or {},
        "silent_drivers": analyze_silent_drivers(answers, lang=lang),
        "z_intent": _call_analyze_intent(answers, lang=lang)
    }
    timings["analysis_ms"] = int((time.perf_counter() - ana_t0) * 1000)

    # 1) KB candidates
    kb_t0 = time.perf_counter()
    cards_struct = _kb_candidates(analysis, answers, lang)
    timings["kb_ms"] = int((time.perf_counter() - kb_t0) * 1000)

    # 2) Fallback LLM لو ناقص
    if len(cards_struct) < 3:
        llm_t0 = time.perf_counter()
        extra = _llm_fallback(user_id, analysis, answers, lang)
        timings["llm_ms"] = int((time.perf_counter() - llm_t0) * 1000)
        cards_struct += extra
    else:
        timings["llm_ms"] = 0

    if not cards_struct:
        cards_struct = [_fallback_identity(i, lang) for i in range(3)]

    # 3) جوده + fill + dedupe
    post_t0 = time.perf_counter()
    cards_struct = _fill_defaults_batch(cards_struct, lang)
    cards_struct = _quality_filter(cards_struct)
    cards_struct = _hard_dedupe_and_fill(cards_struct, lang)
    timings["post_ms"] = int((time.perf_counter() - post_t0) * 1000)

    # 4) Global uniqueness via blacklist
    bl_t0 = time.perf_counter()
    bl = _load_blacklist()
    cards_struct = _ensure_unique_labels_v_global(cards_struct, lang, bl)
    _persist_blacklist(cards_struct, bl)
    timings["blacklist_ms"] = int((time.perf_counter() - bl_t0) * 1000)

    # 5) Scrub URLs (لو فيه)
    scrub_t0 = time.perf_counter()
    cards_struct = [json.loads(scrub_unknown_urls(json.dumps(c, ensure_ascii=False), CFG)) if isinstance(c, dict) else c
                    for c in cards_struct]
    timings["scrub_ms"] = int((time.perf_counter() - scrub_t0) * 1000)

    # 6) Render → List[str] (force-safe strings)
    render_t0 = time.perf_counter()
    rendered = [_format_card(c, lang) for c in cards_struct[:3]]
    rendered = [str(x) for x in rendered]
    timings["render_ms"] = int((time.perf_counter() - render_t0) * 1000)

    timings["total_ms"] = int((time.perf_counter() - t0) * 1000)
    _dbg(
        "egate: {eg}ms | analysis: {ana}ms | kb: {kb}ms | llm: {llm}ms | "
        "post: {post}ms | bl: {bl}ms | scrub: {scrub}ms | render: {render}ms | total: {tot}ms"
        .format(
            eg=timings.get("egate_ms", 0),
            ana=timings.get("analysis_ms", 0),
            kb=timings.get("kb_ms", 0),
            llm=timings.get("llm_ms", 0),
            post=timings.get("post_ms", 0),
            bl=timings.get("blacklist_ms", 0),
            scrub=timings.get("scrub_ms", 0),
            render=timings.get("render_ms", 0),
            tot=timings.get("total_ms", 0),
        )
    )

    # 7) تسجيل اختياري للنتيجة (لن يتسبب في كراش لو الموديول غير موجود)
    try:
        from core.user_logger import log_recommendation_result
        log_recommendation_result(
            user_id=user_id,
            answers=answers,
            recs_text=rendered,
            timings=timings,
            lang=lang,
            model=str(CHAT_MODEL) if 'CHAT_MODEL' in globals() else None,
            app_version=(CFG or {}).get("app_version")
        )
    except Exception:
        pass

    return rendered
