# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
Sport identity recommendations (3 cards) with Layer-Z, first-week (qualitative),
and VR/no-VR variants. Arabic/English.

Order of operation (واقعي أولاً):
1) Evidence Gate (يرفض إن كانت الإجابات غير كافية ويعيد أسئلة متابعة)
2) تحليل واقعي من قاعدة المعرفة:
   - priors + trait_links + guards (من data/sportsync_knowledge.json)
   - قوالب جاهزة لكل label لإخراج بطاقات مكتملة بدون LLM
3) LLM كآخر خيار (fallback) إن ما كفت القاعدة
4) Hard de-dup + URL scrub + Telemetry

قواعد ثابتة:
- ممنوع ذكر الوقت/التكلفة/العدّات/الجولات/المكان المباشر.
- يُسمح بأسماء الرياضات إذا ALLOW_SPORT_NAMES=True
- dedupe محلي وعالمي عبر data/blacklist.json
"""

from __future__ import annotations

import os, json, re, hashlib, importlib
from time import perf_counter, sleep
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

## ========= OpenAI =========
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("أضف الحزمة في requirements: openai>=1.6.1,<2") from e

# نقرأ المفتاح من أكثر من احتمال (OpenAI / OpenRouter / Azure)
OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENROUTER_API_KEY")
    or os.getenv("AZURE_OPENAI_API_KEY")
)

# عنوان الـ Base URL (اختياري مع OpenRouter/Azure)
OPENAI_BASE_URL = (
    os.getenv("OPENAI_BASE_URL")
    or os.getenv("OPENROUTER_BASE_URL")
    or os.getenv("AZURE_OPENAI_ENDPOINT")
)

OPENAI_ORG = os.getenv("OPENAI_ORG")  # غالباً فاضي

OpenAI_CLIENT = None
if OPENAI_API_KEY:
    try:
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL
        if OPENAI_ORG:
            kwargs["organization"] = OPENAI_ORG
        OpenAI_CLIENT = OpenAI(**kwargs)
    except Exception as e:
        print(f"[ENV] ⚠️ فشل إنشاء عميل OpenAI: {e}")
        OpenAI_CLIENT = None
else:
    print("[ENV] ⚠️ لا يوجد API key في المتغيرات البيئية.")

# طباعة حالة الإقلاع للتشخيص
print(
    f"[BOOT] LLM READY? {'YES' if OpenAI_CLIENT else 'NO'} | "
    f"base={OPENAI_BASE_URL or 'default'} | "
    f"model={os.getenv('CHAT_MODEL','gpt-4o-mini')}"
)
# ========= App Config =========
try:
    from core.app_config import get_config
    CFG = get_config()
except Exception:
    CFG = {}

CHAT_MODEL = (CFG.get("llm") or {}).get("model", os.getenv("CHAT_MODEL", "gpt-4o"))
ALLOW_SPORT_NAMES = (CFG.get("recommendations") or {}).get("allow_sport_names", True)

REC_RULES = CFG.get("recommendations") or {}
_MIN_CHARS = int(REC_RULES.get("min_chars", 220))
_REQUIRE_WIN = bool(REC_RULES.get("require_win_condition", True))
_MIN_CORE_SKILLS = int(REC_RULES.get("min_core_skills", 3))

# Evidence Gate thresholds (defaults if not provided)
EGCFG = (CFG.get("analysis") or {}).get("egate", {}) if isinstance(CFG.get("analysis"), dict) else {}
_EG_MIN_ANSWERS = int(EGCFG.get("min_answered", 3))
_EG_MIN_TOTAL_CHARS = int(EGCFG.get("min_total_chars", 120))
_EG_REQUIRED_KEYS = list(EGCFG.get("required_keys", []))  # مثال: ["goal","injury_history"]

# ========= Project imports (with safe fallbacks) =========
try:
    from core.user_logger import log_user_insight
except Exception:
    def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "event") -> None:
        print(f"[LOG:{event_type}] {user_id}: {list(content.keys())}")

# DataPipe (Zapier/Webhook/Disk)
try:
    from core.data_pipe import get_pipe
    _PIPE = get_pipe()
except Exception:
    _PIPE = None

# Security scrubber
try:
    from core.security import scrub_unknown_urls
except Exception:
    def scrub_unknown_urls(text_or_card: str, cfg: Dict[str, Any]) -> str:
        return text_or_card

# Evidence Gate (external) + fallback داخلي
try:
    from core.evidence_gate import evaluate as egate_evaluate
except Exception:
    egate_evaluate = None  # سنستخدم fallback أدناه

# ========= Helpers: Arabic normalization =========
_AR_DIAC = r"[ًٌٍَُِّْـ]"
def _normalize_ar(t: str) -> str:
    if not t: return ""
    t = re.sub(_AR_DIAC, "", t)
    t = t.replace("أ","ا").replace("إ","ا").replace("آ","ا")
    t = t.replace("ؤ","و").replace("ئ","ي")
    t = t.replace("ة","ه").replace("ى","ي")
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ========= Text normalizer (robust for list/dict inputs) =========
def _norm_text(val: Any) -> str:
    """حوّل أي نوع (list/dict/None/tuple/number) إلى نص نظيف."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, (list, tuple)):
        flat: List[str] = []
        for x in val:
            if isinstance(x, (list, tuple)):
                flat.extend(map(str, x))
            else:
                flat.append(str(x))
        return "، ".join([s.strip() for s in flat if s and str(s).strip()])
    if isinstance(val, dict):
        # جرّب مفاتيح شائعة
        for k in ("text", "desc", "value", "answer"):
            if k in val and isinstance(val[k], str):
                return val[k]
        return json.dumps(val, ensure_ascii=False)
    return str(val)

# ========= Soft persona cache =========
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

# ✅ Recommendations cache (optional external import + safe fallback)
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
            _ALIAS_MAP[_normalize_ar(a).lower()] = canon  # تطبيع عربي قبل الحفظ

AL2 = _load_json_safe(AL_PATH)
if isinstance(AL2.get("canonical"), dict):
    for a, canon in AL2["canonical"].items():
        _ALIAS_MAP[_normalize_ar(a).lower()] = canon  # تطبيع عربي قبل الحفظ

# New KB knobs (priors & links & guards & z-intent keywords)
KB_PRIORS: Dict[str, float] = dict(KB.get("priors") or {})
TRAIT_LINKS: Dict[str, Dict[str, float]] = dict(KB.get("trait_links") or {})
GUARDS: Dict[str, Any] = dict(KB.get("guards") or {})
HIGH_RISK_SPORTS: set = set(GUARDS.get("high_risk_sports", []) or [])
KB_ZI: Dict[str, Dict[str, List[str]]] = dict(KB.get("z_intent_keywords") or {})

_FORBIDDEN_GENERIC = set(
    KB.get("guards", {}).get("forbidden_generic_labels", [])
) | set(AL2.get("forbidden_generic", []) or [])

# ========= Analysis import (user traits) =========
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
        except Exception:
            return {"quick_profile": "fallback", "raw_answers": answers}

# ========= Layer Z (silent drivers) =========
try:
    from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    try:
        from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
    except Exception:
        def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
            return ["إنجازات قصيرة", "نفور من التكرار", "تفضيل تحدّي ذهني"]

# ========= Simple keyword signals from answers =========
def _lang_key(lang: str) -> str:
    return "ar" if (lang or "").startswith("الع") else "en"

def _extract_signals(answers: Dict[str, Any], lang: str) -> Dict[str, int]:
    """
    يستخرج إشارات نصّية بسيطة من إجابات المستخدم (solo/team/vr/precision/stealth/…)
    باستخدام z_intent_keywords إن توفّرت.
    """
    blob = " ".join(
        (v.get("answer") if isinstance(v, dict) and "answer" in v else str(v))
        for v in (answers or {}).values()
    )
    blob_l = blob.lower()
    blob_n = _normalize_ar(blob_l)
    res: Dict[str, int] = {}
    zi = KB_ZI.get(_lang_key(lang), {})
    def any_kw(keys: List[str]) -> bool:
        return any((k.lower() in blob_l) or (_normalize_ar(k).lower() in blob_n) for k in keys)
    # إشارات عامة
    if any_kw(zi.get("VR", ["vr","virtual reality","headset","واقع افتراضي","نظاره"])): res["vr"] = 1
    if any_kw(zi.get("دقة/تصويب", []) + zi.get("Precision", []) + ["precision","aim","نشان","دقه"]): res["precision"] = 1
    if any_kw(zi.get("تخفّي", []) + zi.get("Stealth", []) + ["stealth","ظل","تخفي"]): res["stealth"] = 1
    if any_kw(zi.get("قتالي", []) + zi.get("Combat", []) + ["قتال","مبارزه","اشتباك","combat"]): res["combat"] = 1
    if any_kw(zi.get("ألغاز/خداع", []) + zi.get("Puzzles/Feint", []) + ["puzzle","لغز","خدعه"]): res["puzzles"] = 1
    if any_kw(zi.get("فردي", []) + ["solo","وحيد","لوحدي"]): res["solo_pref"] = 1
    if any_kw(zi.get("جماعي", []) + ["team","group","فريق","جماعي"]): res["team_pref"] = 1
    if any_kw(zi.get("هدوء/تنفّس", []) + zi.get("Calm/Breath", []) + ["breath","calm","هدوء","تنفس"]): res["breath"] = 1; res["calm"] = 1
    if any_kw(zi.get("أدرينالين", []) + zi.get("Adrenaline", []) + ["fast","rush","اندفاع"]): res["high_agg"] = 1
    return res

# ========= Intent (Z-intent) =========
def _call_analyze_intent(answers: Dict[str, Any], lang: str="العربية") -> List[str]:
    for modpath in ("core.layer_z_engine", "analysis.layer_z_engine"):
        try:
            mod = importlib.import_module(modpath)
            if hasattr(mod, "analyze_user_intent"):
                return list(mod.analyze_user_intent(answers, lang=lang) or [])
        except Exception:
            pass
    # fallback: بسيط من الإجابات
    intents = set()
    sig = _extract_signals(answers, lang)
    if sig.get("vr"): intents.add("VR")
    if sig.get("stealth"): intents.add("تخفّي")
    if sig.get("puzzles"): intents.add("ألغاز/خداع")
    if sig.get("precision"): intents.add("دقة/تصويب")
    if sig.get("combat"): intents.add("قتالي")
    if sig.get("solo_pref"): intents.add("فردي")
    if sig.get("team_pref"): intents.add("جماعي")
    if sig.get("breath"): intents.add("هدوء/تنفّس")
    if sig.get("high_agg"): intents.add("أدرينالين")
    return list(intents)

# ========= (اختياري) مُشفِّر الإجابات =========
def _extract_profile(answers: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    prof = answers.get("profile") if isinstance(answers, dict) else None
    if isinstance(prof, dict):
        return prof
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
    except Exception:
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
        except Exception:
            pass
    return _egate_fallback(answers, lang=lang)

def _format_followup_card(followups: List[str], lang: str) -> str:
    head = "🧭 نحتاج إجابات قصيرة قبل التوصية" if lang == "العربية" else "🧭 I need a few quick answers first"
    tips = "اكتب سطر واحد لكل سؤال." if lang == "العربية" else "One short line per question."
    lines = [head, "", tips, ""]
    for q in followups:
        lines.append(f"- {q}")
    lines.append("")
    lines.append("أرسل إجاباتك وسنقترح هوية رياضية واضحة فورًا." if lang == "العربية"
                 else "Send your answers and I’ll propose a clear sport-identity right away.")
    return "\n".join(lines)

# ========= Rules & helpers =========
_BLOCKLIST = r"(جري|ركض|سباحة|كرة|قدم|سلة|طائرة|تنس|ملاكمة|كاراتيه|كونغ فو|يوجا|يوغا|بيلاتس|رفع|أثقال|تزلج|دراج|دراجة|ركوب|خيول|باركور|جودو|سكواش|بلياردو|جولف|كرة طائرة|كرة اليد|هوكي|سباق|ماراثون|مصارعة|MMA|Boxing|Karate|Judo|Taekwondo|Soccer|Football|Basketball|Tennis|Swim|Swimming|Running|Run|Cycle|Cycling|Bike|Biking|Yoga|Pilates|Rowing|Row|Skate|Skating|Ski|Skiing|Climb|Climbing|Surf|Surfing|Golf|Volleyball|Handball|Hockey|Parkour|Wrestling)"
_name_re = re.compile(_BLOCKLIST, re.IGNORECASE)

_AVOID_GENERIC = [
    "أي نشاط بدني مفيد","اختر ما يناسبك","ابدأ بأي شيء","جرّب أكثر من خيار",
    "لا يهم النوع","تحرك فقط","نشاط عام","رياضة عامة","أنت تعرف ما يناسبك"
]
_SENSORY = [
    "تنفّس","إيقاع","توتر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","امتداد","حرق لطيف","صفاء","تماسك"
]

_GENERIC_LABELS = {
    "impressive compact", "impressive-compact", "generic sport", "sport identity",
    "movement flow", "basic flow", "simple flow", "body flow"
}

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

def _split_sentences(text: str) -> List[str]:
    if not text: return []
    return [s.strip() for s in re.split(r"(?<=[\.\!\?؟])\s+|[\n،]+", text) if s.strip()]

def _scrub_forbidden(text: str) -> str:
    kept = [s for s in _split_sentences(text) if not _FORBIDDEN_SENT.search(_normalize_ar(s))]
    return "، ".join(kept).strip(" .،")

def _clip(s: str, n: int) -> str:
    if not s: return ""
    s = s.strip()
    return s if len(s) <= n else (s[: max(0, n - 1)] + "…")

def _to_bullets(text_or_list: Any, max_items: int = 6) -> List[str]:
    """
    يرجّع دائمًا List[str] مهما كان الإدخال (string/list/tuple/dict/nested).
    """
    out: List[str] = []

    def _flat_add(x: Any) -> None:
        if x is None:
            return
        # حوّل القوائم/التعشيش إلى نصوص
        if isinstance(x, (list, tuple, set)):
            for y in x:
                _flat_add(y)
            return
        if isinstance(x, dict):
            # خذ أشهر الحقول أولاً، ولو ما لقيتها حوّل الدكت لنص
            for k in ("text", "desc", "value", "answer", "label", "title"):
                if k in x and isinstance(x[k], str) and x[k].strip():
                    out.append(x[k].strip())
                    return
            out.append(json.dumps(x, ensure_ascii=False))
            return
        # أي شيء آخر حوّله لنص ونظّفه
        s = _norm_text(x).strip()
        if s:
            out.append(s)

    _flat_add(text_or_list)

    # لو كان أصلاً string وفيه فواصل/سطور، جزّئه لبنود
    if len(out) == 1 and isinstance(text_or_list, str):
        raw = re.split(r"[;\n\.،]+", out[0])
        out = [i.strip(" -•\t ") for i in raw if i.strip()]

    # قصّ على الحد
    out = out[:max_items]
    # تأكد كلها نصوص 100%
    out = [str(i) for i in out if str(i).strip()]
    return out

# ========= Alignment with Z-axes =========
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
    lab = _canonical_label(label)
    return (lab in _GENERIC_LABELS) or (len(lab) <= 3)

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

    # طبّع جميع الحقول النصية المحتملة (حتى لو كانت list/dict)
    for k in ("sport_label","scene","what_it_looks_like","inner_sensation","why_you",
              "first_week","progress_markers","win_condition","variant_vr","variant_no_vr","vr_idea","mode"):
        if k in r:
            r[k] = _scrub_forbidden(_mask_names(_norm_text(r.get(k))))

    # core_skills → قائمة نصوص نظيفة (بحد أقصى 6)
    cs = r.get("core_skills")
    if isinstance(cs, str):
        parts = [p.strip(" -•\t") for p in re.split(r"[,\n،]+", cs) if p.strip()]
        r["core_skills"] = parts[:6]
    elif isinstance(cs, (list, tuple)):
        skills = [_norm_text(x).strip() for x in cs if _norm_text(x).strip()]
        r["core_skills"] = skills[:6]
    else:
        r["core_skills"] = []

    # difficulty → 1..5
    try:
        d = int(r.get("difficulty", 3))
        r["difficulty"] = max(1, min(5, d))
    except Exception:
        r["difficulty"] = 3

    # mode
    if r.get("mode") not in ("Solo","Team","Solo/Team","فردي","جماعي","فردي/جماعي"):
        r["mode"] = r.get("mode","Solo")
    return r


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

# ========= KB-first: derive traits & score =========
def _derive_binary_traits(analysis: Dict[str, Any], answers: Dict[str, Any], lang: str) -> Dict[str, float]:
    """
    يرجّع {trait_name: strength in [0,1]} بالاعتماد على محاور Z، silent_drivers، والكلمات المفتاحية.
    """
    traits: Dict[str, float] = {}
    prof = (analysis or {}).get("encoded_profile") or {}
    axes = (prof or {}).get("axes") or {}
    silent = set(map(str, (analysis or {}).get("silent_drivers") or []))

    sig = _extract_signals(answers, lang)

    # solo/group -> introvert/extrovert + prefers_*
    sg = float(axes.get("solo_group", 0.0)) if isinstance(axes, dict) else 0.0
    if sg <= -0.35: traits["introvert"] = 1.0; traits["prefers_solo"] = 1.0
    if sg >=  0.35: traits["extrovert"] = 1.0; traits["prefers_team"] = 1.0
    if sig.get("solo_pref"): traits["prefers_solo"] = max(1.0, traits.get("prefers_solo", 0))
    if sig.get("team_pref"): traits["prefers_team"] = max(1.0, traits.get("prefers_team", 0))

    # calm/adrenaline -> calm_regulation / sensation_seeking
    ca = float(axes.get("calm_adrenaline", 0.0)) if isinstance(axes, dict) else 0.0
    if ca <= -0.35 or sig.get("breath"):
        traits["calm_regulation"] = max(traits.get("calm_regulation", 0.0), 0.8)
    if ca >= 0.35 or sig.get("high_agg"):
        traits["sensation_seeking"] = max(traits.get("sensation_seeking", 0.0), 0.8)

    # tech/intu -> precision
    ti = float(axes.get("tech_intuition", 0.0)) if isinstance(axes, dict) else 0.0
    if ti <= -0.35 or sig.get("precision"):
        traits["precision"] = max(traits.get("precision", 0.0), 0.8)

    # تكتيكي/ألغاز/قتالي/VR
    if sig.get("stealth"):
        traits["tactical_mindset"] = max(1.0, traits.get("tactical_mindset", 0))
    if sig.get("puzzles"): traits["likes_puzzles"] = 1.0
    if sig.get("combat"): traits["tactical_mindset"] = max(1.0, traits.get("tactical_mindset", 0))
    vr_i = float((prof or {}).get("vr_inclination", 0.0))
    if sig.get("vr") or vr_i >= 0.4:
        traits["vr_inclination"] = max(traits.get("vr_inclination", 0.0), max(vr_i, 0.8))

    # sustained_attention تقدير بسيط من الهدوء/الألغاز
    if traits.get("calm_regulation", 0) >= 0.8 or traits.get("likes_puzzles", 0) >= 1.0:
        traits["sustained_attention"] = max(traits.get("sustained_attention", 0.0), 0.6)

    # قلق/نفور من التكرار/حاجة مكاسب سريعة
    ar_blob = _normalize_ar(" ".join(_norm_answer_value(v) for v in (answers or {}).values()).lower())
    if any(w in ar_blob for w in ["قلق","مخاوف","توتر شديد","رهاب","خوف"]):
        traits["anxious"] = 1.0
    if any("نفور" in s or "تكرار" in s for s in silent):
        traits["low_repetition_tolerance"] = 1.0
    if any("انجازات قصيره" in _normalize_ar(s) for s in silent):
        traits["needs_quick_wins"] = 1.0

    return traits

def _score_candidates_from_links(traits: Dict[str, float]) -> List[Tuple[float, str]]:
    """
    score(label) = prior[label] + Σ (trait_strength * link_weight)
    مع احترام الحراس (anxiety vs high-risk).
    """
    anxious = traits.get("anxious", 0.0) >= 0.8 and GUARDS.get("no_high_risk_for_anxiety", True)

    labels = set(KB_PRIORS.keys())
    for t, mapping in (TRAIT_LINKS or {}).items():
        labels.update(mapping.keys())

    scored: List[Tuple[float, str]] = []
    for label in labels:
        if anxious and label in HIGH_RISK_SPORTS:
            scored.append((-1e9, label))
            continue
        s = float(KB_PRIORS.get(label, 0.0))
        for t_name, strength in traits.items():
            link = (TRAIT_LINKS.get(t_name) or {}).get(label, 0.0)
            if link:
                s += float(strength) * float(link)
        scored.append((s, label))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

# ========= Optional: identities from KB (if provided) =========
def _pick_kb_recommendations(user_axes: Dict[str, Any], user_signals: Dict[str, int], lang: str) -> List[Dict[str, Any]]:
    """
    لو ملف KB يحوي "identities": نقدر نفلتر/نرتّب بناءً على محاذاة بسيطة.
    إن لم يوجد يرجع [].
    """
    identities = KB.get("identities")
    if not isinstance(identities, list) or not identities:
        return []
    scored: List[Tuple[float, Dict[str, Any]]] = []
    exp = _axes_expectations(user_axes or {}, lang)
    for rec in identities:
        r = _sanitize_record(rec)
        blob = " ".join([_norm_text(r.get("what_it_looks_like","")),
                         _norm_text(r.get("why_you","")),
                         _norm_text(r.get("first_week",""))]).lower()
        hit = 0
        for words in exp.values():
            if words and any(w.lower() in blob for w in words):
                hit += 1
        # إشارات نصية
        if user_signals.get("precision") and ("precision" in blob or "دقه" in blob): hit += 1
        if user_signals.get("stealth") and ("stealth" in blob or "تخفي" in blob): hit += 1
        scored.append((hit, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:3]]

# ========= Templates by label (AR/EN) =========
def _canon_label(label: str) -> str:
    lab = _normalize_ar((label or "")).lower().strip(" -—:،")
    if not lab:
        return ""
    if lab in _ALIAS_MAP:
        return _ALIAS_MAP[lab]
    lab = re.sub(r"[^a-z0-9\u0600-\u06FF]+", " ", lab)
    lab = re.sub(r"\s+", " ", lab).strip()
    return lab

def _is_forbidden_generic(label: str) -> bool:
    base = _normalize_ar((label or "")).lower()
    return any(g in base for g in _FORBIDDEN_GENERIC)

if L in (_canon_label("esports"),):
    return _sanitize_record(_fill_defaults({
        "sport_label": "Esports — دقة وتكتيك" if ar else "Esports — Precision & Tactics",
        "what_it_looks_like": "تصويب لحظي وقراءة مواقف وتنسيق فريق/فرد.",
        "inner_sensation": "تيقّظ مع هدوء قرار.",
        "why_you": "تستمتع بالدقة والذكاء التكتيكي.",
        "first_week": "تثبيت حسّ النظر — إدارة الإيقاع — قرار نظيف.",
        "progress_markers": "ثبات تصويب — أخطاء أقل.",
        "win_condition": "تحقيق أهداف تكتيكية ضمن سيناريو محاكاة.",
        "core_skills": ["تتبّع نظرة","قرار سريع","تنسيق"] if ar else
                       ["gaze tracking","snap decision","coordination"],
        "mode": "Solo/Team",
        "variant_vr": "سيناريو تكتيكي افتراضي.",
        "variant_no_vr": "تمارين دقة قصيرة.",  # ← هذا هو التصحيح
        "difficulty": 3
    }, lang))

    # خرائط جاهزة للخمسة "الهويات" الداخلية
    KB_PRESETS = {
        "tactical_immersive_combat": _fallback_identity(0, lang),
        "stealth_flow_missions": _fallback_identity(1, lang),
        "mind_trap_puzzles": _fallback_identity(2, lang),
        "range_precision_circuit": _fallback_identity(3, lang),
        "grip_balance_ascent": _fallback_identity(4, lang),
    }
    for k, v in KB_PRESETS.items():
        if L == _canon_label(k):
            return _sanitize_record(_fill_defaults(v, lang))

    # رياضات شائعة
    if L in (_canon_label("archery"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "الرماية (دقة)" if ar else "Archery (Precision)",
            "what_it_looks_like": "وضع ثابت ونظرة مركّزة وانتقال منظّم لهدف بصري.",
            "inner_sensation": "هدوء ونبض مستقر وثقة يد.",
            "why_you": "تميل للدقة والتنظيم وقرارات هادئة.",
            "first_week": "ثبّت النظرة — اضبط النفس — بدّل زواياك بسلاسة.",
            "progress_markers": "ثبات يد أوضح — قرارات أنظف — توتر أقل.",
            "win_condition": "تحقيق دقة متّسقة على سلسلة أهداف.",
            "core_skills": ["تثبيت نظرة","ضبط نفس","انتقال زوايا","تحكّم دقيق"] if ar else
                           ["gaze hold","breath control","angle transitions","fine control"],
            "mode": "Solo",
            "variant_vr": "لوحة أهداف افتراضية مع ارتجاع بصري.",
            "variant_no_vr": "أهداف إسفنجية آمنة.",
            "difficulty": 2
        }, lang))
    if L in (_canon_label("marksmanship"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "تصويب آمن (مدى)" if ar else "Marksmanship (Safe Range)",
            "what_it_looks_like": "وقفة ثابتة، تنفّس هادئ، قرار نظيف على مؤشرات بصرية.",
            "inner_sensation": "تركيز متمركز وثبات يد.",
            "why_you": "تبحث عن وضوح القرار ودقّة هادئة.",
            "first_week": "تنسيق نظرة-نفس — دخول وخروج قرار دون ارتباك.",
            "progress_markers": "تشتت أقل — تماسك قرار — اتساق أعلى.",
            "win_condition": "سلسلة إصابات ضمن هامش دقة محدد.",
            "core_skills": ["ثبات","تنفّس","قراءة مؤشرات","قرار هادئ"] if ar else
                           ["stability","breathing","cue reading","calm decision"],
            "mode": "Solo",
            "variant_vr": "محاكاة تصويب آمنة.",
            "variant_no_vr": "لوحات إسفنجية/ليزر تدريبية.",
            "difficulty": 2
        }, lang))
    if L in (_canon_label("climbing"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "تسلق — قبضة وتوازن" if ar else "Climbing — Grip & Balance",
            "what_it_looks_like": "قراءة مسكات وتحويل وزن هادئ ومسار صاعد منظّم.",
            "inner_sensation": "تماسك داخلي وثقة حركة.",
            "why_you": "تحب تحدّي تحكّم الجسد بلا ضجيج.",
            "first_week": "اقرأ المسكة — حرّر وزنك — تحرّك ببطء صاعد.",
            "progress_markers": "تعب ساعد أقل — اتزان أوضح.",
            "win_condition": "الوصول للنقطة الهدف دون إفلات.",
            "core_skills": ["قبضة","توازن","تحويل وزن","قراءة مسار"] if ar else
                           ["grip","balance","weight shift","route reading"],
            "mode": "Solo",
            "variant_vr": "مسارات قبضات افتراضية.",
            "variant_no_vr": "عناصر قبضة آمنة خفيفة.",
            "difficulty": 2
        }, lang))
    if L in (_canon_label("swimming"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "سباحة — خطوط هادئة" if ar else "Swimming — Calm Lines",
            "what_it_looks_like": "سكتات منتظمة وتوافق نفس-حركة.",
            "inner_sensation": "انسياب وهدوء ذهني.",
            "why_you": "تبحث عن صفاء وتنظيم إيقاع.",
            "first_week": "لاحظ الإيقاع — نظّم الزفير — ثبّت خط الجسم.",
            "progress_markers": "توتر أقل — سلاسة أعلى — إيقاع متسق.",
            "win_condition": "اتساق الإيقاع والمحاذاة عبر مجموعة أطوال.",
            "core_skills": ["محاذاة جسم","تنفّس منظم","إيقاع ثابت"] if ar else
                           ["body alignment","paced breathing","steady rhythm"],
            "mode": "Solo",
            "variant_vr": "تخيّل بصري للتنفس والمحاذاة.",
            "variant_no_vr": "تمارين محاذاة وتنفس على اليابسة.",
            "difficulty": 2
        }, lang))
    if L in (_canon_label("distance_running"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "جري مسافات — إيقاع ثابت" if ar else "Distance Running — Steady Rhythm",
            "what_it_looks_like": "خطوة منتظمة ونَفَس موزون وانتباه للإيقاع.",
            "inner_sensation": "صفاء وحضور جسدي بسيط.",
            "why_you": "تفضّل تقدمًا هادئًا ومؤشرات واضحة.",
            "first_week": "ابنِ إيقاعك — راقب النفس — خفّف توتر الكتفين.",
            "progress_markers": "نعومة خطوة — صفاء ذهني — قرار أهدأ.",
            "win_condition": "حفظ الإيقاع دون انقطاع على مسار محدد.",
            "core_skills": ["إيقاع","تنفّس","استرخاء كتف","محاذاة"] if ar else
                           ["rhythm","breath","shoulder relax","alignment"],
            "mode": "Solo",
            "variant_vr": "مؤشرات إيقاع افتراضية.",
            "variant_no_vr": "تمارين إيقاع على أرض مسطحة.",
            "difficulty": 2
        }, lang))
    if L in (_canon_label("tennis"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "تنس — زوايا ورِد" if ar else "Tennis — Angles & Rally",
            "what_it_looks_like": "تبادل كُرات بزوايا محسوبة وتوقيت نظيف للضربة.",
            "inner_sensation": "يقظة خفيفة مع قرار واضح.",
            "why_you": "توازن اجتماعي/فردي مع دقّة لحظية.",
            "first_week": "ثبّت النظرة — توقيت الضربة — اقرأ الزاوية.",
            "progress_markers": "تصويب أنظف — ردّ فعل أوضح.",
            "win_condition": "سلسلة تبادلات ناجحة بزوايا محسوبة.",
            "core_skills": ["توقيت","زاوية","توازن","قرار"] if ar else
                           ["timing","angle","balance","decision"],
            "mode": "Solo/Team",
            "variant_vr": "رالي افتراضي تفاعلي.",
            "variant_no_vr": "حائط ردّ/شريك تدريب.",
            "difficulty": 3
        }, lang))
    if L in (_canon_label("yoga"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "يوغا — تنظيم نفس ومحاذاة" if ar else "Yoga — Breath & Alignment",
            "what_it_looks_like": "سلاسل محاذاة هادئة وتركيز تنفّس.",
            "inner_sensation": "صفاء وتماسك داخلي.",
            "why_you": "تبحث عن تهدئة الأعصاب ووعي جسدي.",
            "first_week": "محاذاة أساسية — مراقبة زفير — نعومة انتقال.",
            "progress_markers": "توتر أقل — وعي مفصلي أفضل.",
            "win_condition": "حفظ المحاذاة والتنفس عبر تسلسل كامل.",
            "core_skills": ["تنفّس","محاذاة","اتزان"] if ar else
                           ["breath","alignment","balance"],
            "mode": "Solo",
            "variant_vr": "إرشاد بصري للتنفس والمحاذاة.",
            "variant_no_vr": "سلسلة وضعيات أساسية.",
            "difficulty": 1
        }, lang))
    if L in (_canon_label("free_diving"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "غوص حر — هدوء وتنظيم" if ar else "Free Diving — Calm Regulation",
            "what_it_looks_like": "تحضير تنفّس دقيق وهدوء داخلي.",
            "inner_sensation": "سكون وتركيز عالي.",
            "why_you": "تركّز على ضبط النفس والهدوء.",
            "first_week": "جولات نفس منضبط وتخيّل هادئ.",
            "progress_markers": "صفاء أعلى — تحكم نفسي أعمق.",
            "win_condition": "حفظ هدوء وتنفس منظم خلال مهمة محاكاة.",
            "core_skills": ["ضبط نفس","تركيز","استرخاء"] if ar else
                           ["breath control","focus","relaxation"],
            "mode": "Solo",
            "variant_vr": "محاكاة نفس وغمر بصري.",
            "variant_no_vr": "بروتوكول تنفّس جاف آمن.",
            "difficulty": 3
        }, lang))
    if L in (_canon_label("chess"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "شطرنج — تكتيك ذهني" if ar else "Chess — Tactical Mind",
            "what_it_looks_like": "مناورات هادئة وقراءة زوايا قرار.",
            "inner_sensation": "فضول ذهني وثقة هادئة.",
            "why_you": "تحب الألغاز والتكتيك.",
            "first_week": "نمط افتتاح ثابت — قراءة تهديدات — هدوء قبل القرار.",
            "progress_markers": "أخطاء أقل — وضوح خطّة.",
            "win_condition": "إنهاء لعبة بخطّة واضحة دون أخطاء متتالية.",
            "core_skills": ["قراءة تهديد","صبر","خدعة بصرية"] if ar else
                           ["threat reading","patience","feint"],
            "mode": "Solo/Team",
            "variant_vr": "لوح افتراضي تفاعلي.",
            "variant_no_vr": "سيناريوهات تكتيكية قصيرة.",
            "difficulty": 2
        }, lang))
    if L in (_canon_label("esports"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "Esports — دقة وتكتيك" if ar else "Esports — Precision & Tactics",
            "what_it_looks_like": "تصويب لحظي وقراءة مواقف وتنسيق فريق/فرد.",
            "inner_sensation": "تيقّظ مع هدوء قرار.",
            "why_you": "تستمتع بالدقة والذكاء التكتيكي.",
            "first_week": "تثبيت حسّ النظر — إدارة الإيقاع — قرار نظيف.",
            "progress_markers": "ثبات تصويب — أخطاء أقل.",
            "win_condition": "تحقيق أهداف تكتيكية ضمن سيناريو محاكاة.",
            "core_skills": ["تتبّع نظرة","قرار سريع","تنسيق"] if ar else
                           ["gaze tracking","snap decision","coordination"],
            "mode": "Solo/Team",
            "variant_vr": "سيناريو تكتيكي افتراضي.",
            "variant_no_vr": "تمارين دقة قصيرة.",  # FIXED
            "difficulty": 3
        }, lang))
    if L in (_canon_label("football"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "كرة قدم — زوايا وتمرير" if ar else "Football — Angles & Passing",
            "what_it_looks_like": "تحرّك جماعي وقراءة مساحات.",
            "inner_sensation": "اندماج جماعي مع قرار لحظي.",
            "why_you": "تميل للتعاون والمنافسة الجماعية.",
            "first_week": "قراءة زاوية التمرير — دعم بدون كرة.",
            "progress_markers": "تمركز أفضل — قرارات أسرع.",
            "win_condition": "تنفيذ مهمّة تكتيكية ضمن سيناريو.",
            "core_skills": ["تمركز","زاوية","دعم","قرار"] if ar else
                           ["positioning","angle","support","decision"],
            "mode": "Team",
            "variant_vr": "تكتيك تمركز افتراضي.",
            "variant_no_vr": "سيناريوهات زوايا على مسار محدد.",
            "difficulty": 3
        }, lang))
    if L in (_canon_label("basketball"),):
        return _sanitize_record(_fill_defaults({
            "sport_label": "سلة — مساحات وإيقاع" if ar else "Basketball — Space & Rhythm",
            "what_it_looks_like": "تحرّكات قصيرة وزوايا تمرير/تصويب.",
            "inner_sensation": "يقظة وإيقاع جماعي.",
            "why_you": "تفضّل التفاعل السريع الجماعي.",
            "first_week": "قراءة مساحة — توقيت قطع — قرار هادئ.",
            "progress_markers": "تمركز أوضح — أخطاء أقل.",
            "win_condition": "سلسلة لعبات ناجحة ضمن مخطط.",
            "core_skills": ["زاوية","توقيت","توازن","قرار"] if ar else
                           ["angle","timing","balance","decision"],
            "mode": "Team",
            "variant_vr": "مخططات لعب افتراضية.",
            "variant_no_vr": "تمارين زوايا بدون أدوات.",
            "difficulty": 3
        }, lang))

    return None

# ====== Blacklist (persistent, JSON) =========================================
def _load_blacklist() -> dict:
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
    if not c:
        return
    rec = bl["labels"].get(c, {"aliases": [], "count": 0, "first_seen": None})
    if alias and alias not in rec["aliases"]:
        rec["aliases"].append(alias)
    rec["count"] = int(rec.get("count", 0)) + 1
    if not rec.get("first_seen"):
        rec["first_seen"] = datetime.utcnow().isoformat() + "Z"
    rec["last_used"] = datetime.utcnow().isoformat() + "Z"
    bl["labels"][c] = rec

_AR_VARIANTS = [
    "نسخة ظلّية", "نمط مراوغة", "خط تحكّم هادئ", "نسخة تفكيك تكتيكي",
    "مناورة عكسية", "زاوية صامتة", "طيف التتبع", "تدفق خفي"
]
_EN_VARIANTS = [
    "Shadow Variant", "Evasive Pattern", "Calm-Control Line", "Tactical Deconstruction",
    "Counter-Maneuver", "Silent Angle", "Tracking Flux", "Stealth Flow"
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
    for r in recs:
        lab = r.get("sport_label") or ""
        if lab.strip():
            _bl_add(bl, lab, alias=lab)
    _save_json_atomic(BL_PATH, bl)

# ========= Prompt Builder (LLM) =========
def _style_seed(user_id: str, profile: Optional[Dict[str, Any]]) -> int:
    base = user_id or "anon"
    axes = profile.get("axes", {}) if isinstance(profile, dict) else {}
    s = f"{base}:{json.dumps(axes, sort_keys=True, ensure_ascii=False)}"
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

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

def _strip_code_fence(s: str) -> str:
    if not s: return s
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s

def _json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                 personality: Any, lang: str, style_seed: int) -> List[Dict[str, str]]:
    bullets = _answers_to_bullets(answers)
    persona = personality if isinstance(personality, str) else json.dumps(personality, ensure_ascii=False)
    profile = analysis.get("encoded_profile") or {}
    compact_analysis = _compact_analysis_for_prompt(analysis, profile)

    comp_blob = json.dumps(compact_analysis, ensure_ascii=False)
    if len(comp_blob) > MAX_PROMPT_CHARS:
        compact_analysis = {"z_axes": compact_analysis.get("z_axes", {}), "z_intent": compact_analysis.get("z_intent", [])}

    axis = compact_analysis.get("z_axes", {})
    exp = _axes_expectations(axis, lang)
    exp_lines = []
    if exp:
        title = {"calm_adrenaline":"هدوء/أدرينالين","solo_group":"فردي/جماعي","tech_intuition":"تقني/حدسي"} \
                if lang=="العربية" else \
                {"calm_adrenaline":"Calm/Adrenaline","solo_group":"Solo/Group","tech_intuition":"Technical/Intuitive"}
        for k, words in exp.items():
            if words:
                exp_lines.append(f"{title[k]}: {', '.join(words)}")
    axis_hint = ("\n".join(exp_lines)) if exp_lines else ""

    z_intent = compact_analysis.get("z_intent", [])
    intent_hint = ("، ".join(z_intent) if lang=="العربية" else ", ".join(z_intent)) if z_intent else ""

    if lang == "العربية":
        sys = (
            "أنت مدرّب SportSync AI بنبرة إنسانية لطيفة (صديق محترف).\n"
            "ممنوع ذكر (الوقت/التكلفة/العدّات/الجولات/الدقائق/المكان المباشر).\n"
            "سَمِّ 'هوية/رياضة' واضحة عند الحاجة.\n"
            "أعِد JSON فقط."
        )
        usr = (
            "حوّل بيانات المستخدم إلى ثلاث توصيات «هوية رياضية واضحة». "
            "أعِد JSON بالمفاتيح: "
            "{\"recommendations\":[{"
            "\"sport_label\":\"...\",\"what_it_looks_like\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\"," 
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"win_condition\":\"...\"," 
            "\"core_skills\":[\"...\",\"...\"],\"mode\":\"Solo/Team\",\"variant_vr\":\"...\",\"variant_no_vr\":\"...\",\"difficulty\":1-5"
            "}]} "
            "قواعد إلزامية: اذكر win_condition و 3–5 core_skills على الأقل. "
            "حاذِ Z-axes بالكلمات التالية إن أمكن:\n" + axis_hint +
            ("\n\n— نوايا Z المحتملة: " + intent_hint if intent_hint else "") + "\n\n"
            f"— شخصية المدرب:\n{persona}\n\n"
            "— تحليل موجز:\n" + json.dumps(compact_analysis, ensure_ascii=False) + "\n\n"
            "— إجابات موجزة:\n" + bullets + "\n\n"
            f"— style_seed: {style_seed}\n"
            "أعِد JSON فقط."
        )
    else:
        sys = (
            "You are a warm, human SportSync coach. "
            "No time/cost/reps/sets/minutes/place. Name the sport/identity if clarity needs it. JSON only."
        )
        usr = (
            "Create THREE clear sport-like identities with required keys: "
            "{\"recommendations\":[{\"sport_label\":\"...\",\"what_it_looks_like\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\"," 
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"win_condition\":\"...\",\"core_skills\":[\"...\"]," 
            "\"mode\":\"Solo/Team\",\"variant_vr\":\"...\",\"variant_no_vr\":\"...\",\"difficulty\":1-5}]}"
            " Align with Z-axes using words:\n" + axis_hint +
            ( "\n\n— Z intents: " + intent_hint if intent_hint else "" ) + "\n\n"
            f"— Coach persona:\n{persona}\n— Compact analysis:\n" + json.dumps(compact_analysis, ensure_ascii=False) + "\n"
            "— Bulleted answers:\n" + bullets + f"\n— style_seed: {style_seed}\nJSON only."
        )
    return [{"role": "system", "content": sys}, {"role": "user", "content": usr}]

def _parse_json(text: str) -> Optional[List[Dict[str, Any]]]:
    if not text:
        return None
    text = _strip_code_fence(text)
    try:
        obj = json.loads(text)
        recs = obj.get("recommendations", [])
        if isinstance(recs, list) and recs:
            return recs
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text or "")
    if m:
        try:
            obj = json.loads(m.group(0))
            recs = obj.get("recommendations", [])
            if isinstance(recs, list) and recs:
                return recs
        except Exception:
            pass
    return None

def _to_bullets(text_or_list: Any, max_items: int = 6) -> List[str]:
    if text_or_list is None:
        return []
    if isinstance(text_or_list, (list, tuple)):
        items = [str(i).strip(" -•\t ") for i in text_or_list if str(i).strip()]
        return items[:max_items]
    text = str(text_or_list)
    raw = re.split(r"[;\n\.،]+", text)
    items = [i.strip(" -•\t ") for i in raw if i.strip()]
    return items[:max_items]

def _one_liner(*parts: str, max_len: int = 140) -> str:
    s = " — ".join([p.strip() for p in parts if p and p.strip()])
    return s[:max_len]

def _format_card(rec: Dict[str, Any], i: int, lang: str) -> str:
    head_ar = ["🟢 التوصية رقم 1","🌿 التوصية رقم 2","🔮 التوصية رقم 3 (ابتكارية)"]
    head_en = ["🟢 Recommendation 1","🌿 Recommendation 2","🔮 Recommendation 3 (Creative)"]
    head = (head_ar if lang == "العربية" else head_en)[i]

    label = _norm_text(rec.get("sport_label") or "")
    scene = _norm_text(rec.get("what_it_looks_like") or rec.get("scene") or "")
    inner = _norm_text(rec.get("inner_sensation") or "")
    why   = _norm_text(rec.get("why_you") or "")
    week  = _to_bullets(rec.get("first_week") or "")
    prog  = _to_bullets(rec.get("progress_markers") or "", max_items=4)
    win   = _norm_text(rec.get("win_condition") or "")
    skills= rec.get("core_skills") or []
    diff  = rec.get("difficulty", 3)
    mode  = _norm_text(rec.get("mode") or "Solo")
    vr    = _norm_text(rec.get("variant_vr") or rec.get("vr_idea") or "")
    novr  = _norm_text(rec.get("variant_no_vr") or "")

    intro = _one_liner(scene, inner)

    if lang == "العربية":
        out = [head, ""]
        if label: out.append(f"🎯 الهوية المثالية لك: {label}")
        if intro: out += ["\n💡 ما هي؟", f"- {intro}"]
        if why:
            out += ["\n🎮 ليه تناسبك؟"]
            for b in _to_bullets(why, 4) or [why]: out.append(f"- {b}")
        if skills:
            out += ["\n🧩 مهارات أساسية:"]
            for s in [ _norm_text(x) for x in skills[:5] ]: out.append(f"- {s}")
        if win: out += ["\n🏁 كيف تفوز؟", f"- {win}"]
        if week:
            out += ["\n🚀 أول أسبوع (نوعي):"]
            for b in week: out.append(f"- {b}")
        if prog:
            out += ["\n✅ علامات تقدم محسوسة:"]
            for b in prog: out.append(f"- {b}")
        notes = []
        if mode: notes.append(("وضع اللعب: " + mode))
        if novr: notes.append("بدون VR: " + novr)
        if vr: notes.append("VR (اختياري): " + vr)
        if notes:
            out += ["\n👁‍🗨 ملاحظات:", f"- " + "\n- ".join(notes)]
        out.append(f"\nالمستوى التقريبي: {diff}/5")
        return "\n".join(out)

    else:
        out = [head, ""]
        if label: out.append(f"🎯 Ideal identity: {label}")
        if intro: out += ["\n💡 What is it?", f"- {intro}"]
        if why:
            out += ["\n🎮 Why you"]
            for b in _to_bullets(why, 4) or [why]: out.append(f"- {b}")
        if skills:
            out += ["\n🧩 Core skills:"]
            for s in [ _norm_text(x) for x in skills[:5] ]: out.append(f"- {s}")
        if win: out += ["\n🏁 Win condition", f"- {win}"]
        if week:
            out += ["\n🚀 First week (qualitative)"]
            for b in week: out.append(f"- {b}")
        if prog:
            out += ["\n✅ Progress cues"]
            for b in prog: out.append(f"- {b}")
        notes = []
        if mode: notes.append(("Mode: " + mode))
        if novr: notes.append("No-VR: " + novr)
        if vr: notes.append("VR (optional): " + vr)
        if notes:
            out += ["\n👁‍🗨 Notes:", f"- " + "\n- ".join(notes)]
        out.append(f"\nApprox level: {diff}/5")
        return "\n".join(out)
    else:
        out = [head, ""]
        if label: out.append(f"🎯 Ideal identity: {label}")
        if intro: out += ["\n💡 What is it?", f"- {intro}"]
        if why:
            out += ["\n🎮 Why you"]
            for b in _to_bullets(why, 4) or [why]: out.append(f"- {b}")
        if skills:
            out += ["\n🧩 Core skills:"]
            for s in skills[:5]: out.append(f"- {s}")
        if win: out += ["\n🏁 Win condition", f"- {win}"]
        if week:
            out += ["\n🚀 First week (qualitative)"]
            for b in week: out.append(f"- {b}")
        if prog:
            out += ["\n✅ Progress cues"]
            for b in prog: out.append(f"- {b}")
        notes = []
        if mode: notes.append(("Mode: " + mode))
        if novr: notes.append("No-VR: " + novr)
        if vr: notes.append("VR (optional): " + vr)
        if notes:
            out += ["\n👁‍🗨 Notes:", f"- " + "\n- ".join(notes)]
        out.append(f"\nApprox level: {diff}/5")
        return "\n".join(out)

def _sanitize_fill(recs: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    """
    تنظّف وتكمّل التوصيات القادمة من الـKB أو الـLLM وتمنع الأخطاء الناتجة من
    وجود قوائم/ديكشنري داخل الحقول النصية.
    """
    temp: List[Dict[str, Any]] = []
    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        r = _fill_defaults(_sanitize_record(r), lang)

        # تأكد أن كل القيم نصوص قبل الـ join
        vals = [
            _norm_text(r.get("sport_label","")),
            _norm_text(r.get("what_it_looks_like","")),
            _norm_text(r.get("why_you","")),
            _norm_text(r.get("first_week","")),
            _norm_text(r.get("progress_markers","")),
            _norm_text(r.get("win_condition","")),
        ]
        blob = " ".join(vals)

        if _too_generic(blob, _MIN_CHARS) or not _has_sensory(blob) or not _is_meaningful(r) \
           or (_REQUIRE_WIN and not r.get("win_condition")) \
           or len(r.get("core_skills") or []) < _MIN_CORE_SKILLS \
           or _label_is_generic(r.get("sport_label","")):
            r = _fallback_identity(i, lang)

        temp.append(r)

    return _hard_dedupe_and_fill(temp, lang)

# ========= OpenAI helper with timeout + retry =========
def _chat_with_retry(messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
    """
    ينفّذ مكالمة واحدة مع مهلة REC_BUDGET_S وريترای ذكي (تقليص التوكنز + موديل احتياطي).
    """
    if OpenAI_CLIENT is None:
        raise RuntimeError("OPENAI_API_KEY غير مضبوط")

    attempts = 4 if not REC_FAST_MODE else 3
    last_err = None
    model_local = CHAT_MODEL
    max_tokens_local = max_tokens

    timeout_s = max(4.0, min(REC_BUDGET_S, 26.0))
    client = OpenAI_CLIENT.with_options(timeout=timeout_s)

    for i in range(1, attempts + 1):
        try:
            resp = client.chat.completions.create(
                model=model_local,
                messages=messages,
                temperature=temperature,
                top_p=0.9,
                presence_penalty=0.15,
                frequency_penalty=0.1,
                max_tokens=max_tokens_local
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            last_err = e
            es = (str(e) or "").lower()
            if any(t in es for t in ["timeout", "rate limit", "overloaded", "503", "504", "gateway", "temporar"]):
                sleep(min(1.2 * i, 2.5))
                max_tokens_local = max(256, int(max_tokens_local * 0.75))
                if i == attempts - 1 and model_local != CHAT_MODEL_FALLBACK:
                    model_local = CHAT_MODEL_FALLBACK
                continue
            break
    raise RuntimeError(f"LLM call failed after retries: {last_err}")

# ========= PUBLIC API =========
def generate_sport_recommendation(answers: Dict[str, Any],
                                  lang: str = "العربية",
                                  user_id: str = "N/A",
                                  job_id: str = "") -> List[str]:
    t0 = perf_counter()

    # ✅ كاش
    try:
        cached_cards = get_cached_recommendation(user_id, answers, lang)
    except TypeError:
        try:
            cached_cards = get_cached_recommendation(user_id)  # type: ignore
        except Exception:
            cached_cards = None
    if cached_cards:
        _dbg("cache HIT for recommendations")
        return cached_cards
    _dbg("cache MISS for recommendations")

    # Evidence Gate
    eg = _run_egate(answers or {}, lang=lang)
    if _PIPE:
        try:
            _PIPE.send(
                event_type="egate_decision",
                payload={
                    "status": eg.get("status"),
                    "answered": eg.get("answered"),
                    "total_chars": eg.get("total_chars"),
                    "required_missing": eg.get("required_keys", []) or eg.get("required_missing", []),
                    "job_id": job_id
                },
                user_id=user_id, lang=("العربية" if lang=="العربية" else "English"),
                model=CHAT_MODEL
            )
        except Exception:
            pass

    if eg.get("status") != "pass":
        card = _format_followup_card(eg.get("followup_questions", []), lang=lang)
        try:
            sec = (CFG.get("security") or {})
            if sec.get("scrub_urls", True):
                card = scrub_unknown_urls(card, CFG)
        except Exception:
            pass
        return [card, "—", "—"]

    # تحليل المستخدم + طبقة Z + Intent + profile
    analysis: Dict[str, Any] = _call_analyze_user_from_answers(user_id, answers, lang)
    try:
        analysis["silent_drivers"] = analyze_silent_drivers(answers, lang=lang) or []
    except Exception:
        analysis["silent_drivers"] = []
    try:
        z_intent = _call_analyze_intent(answers, lang=lang) or []
        if z_intent: analysis["z_intent"] = z_intent
    except Exception:
        pass
    profile = _extract_profile(answers, lang)
    if profile:
        analysis["encoded_profile"] = profile
        if "axes" in profile: analysis["z_axes"] = profile["axes"]
        if "scores" in profile: analysis["z_scores"] = profile["scores"]

    # ======== KB-first (priors + trait_links + guards + templates) ========
    user_axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    user_signals = _extract_signals(answers, lang)

    # (A) identities من KB إن وجدت
    kb_recs = _pick_kb_recommendations(user_axes, user_signals, lang)

    # (B) إن لم تكفِ، استخدم trait_links
    if len(kb_recs) < 3 and (KB_PRIORS or TRAIT_LINKS):
        trait_strengths = _derive_binary_traits(analysis, answers, lang)
        ranked = _score_candidates_from_links(trait_strengths)

        picked: List[Dict[str, Any]] = []
        used = set()
        for _, lbl in ranked:
            if len(picked) >= 3: break
            c = _canon_label(lbl)
            if c in used: continue
            tpl = _template_for_label(lbl, lang)
            if not tpl:
                tpl = _fallback_identity(len(picked), lang)  # كحلّ أخير داخل مسار KB
            picked.append(tpl)
            used.add(c)
        kb_recs.extend(picked)
        kb_recs = kb_recs[:3]

    if len(kb_recs) >= 3:
        kb_recs = _sanitize_fill(kb_recs, lang)
        bl = _load_blacklist()
        kb_recs = _ensure_unique_labels_v_global(kb_recs, lang, bl)
        _persist_blacklist(kb_recs, bl)
        cards = [_format_card(kb_recs[i], i, lang) for i in range(3)]
        try:
            sec = (CFG.get("security") or {})
            if sec.get("scrub_urls", True):
                cards = [scrub_unknown_urls(c, CFG) for c in cards]
        except Exception:
            pass
        try:
            log_user_insight(
                user_id=user_id,
                content={
                    "language": lang,
                    "answers": {k: v for k, v in (answers or {}).items() if k != "profile"},
                    "analysis": analysis,
                    "source": "KB/trait_links" if (KB_PRIORS or TRAIT_LINKS) else "KB",
                    "seed": _style_seed(user_id, profile or {}),
                    "elapsed_s": round(perf_counter() - t0, 3),
                    "fast_mode": REC_FAST_MODE,
                    "job_id": job_id
                },
                event_type="kb_recommendation"
            )
        except Exception:
            pass
        try:
            save_cached_recommendation(user_id, answers, lang, cards)
        except Exception:
            pass
        return cards

       # ======== LLM كآخر خيار ========
    # لو ما فيه عميل LLM، رجّع رسالة تشخيص واضحة
    if OpenAI_CLIENT is None:
        _dbg("[LLM] client=None -> fallback card")
        return [
            "❌ لا يمكن استدعاء النموذج الآن. ثبّت OPENAI_API_KEY (أو OPENROUTER_API_KEY/AZURE_OPENAI_API_KEY) على الخادم وأعد التشغيل.",
            "—",
            "—"
        ]

    # شخصية المدرب (كاش)
    persona = get_cached_personality(analysis, lang=lang)
    if not persona:
        persona = {
            "name":"SportSync Coach",
            "tone":"حازم-هادئ",
            "style":"حسّي واقعي إنساني",
            "philosophy":"هوية حركة بلا أسماء مع وضوح هويّة"
        }
        try:
            save_cached_personality(analysis, persona, lang=lang)
        except Exception:
            pass

    # بناء البرومبت واستدعاء النموذج
    seed = _style_seed(user_id, profile or {})
    msgs = _json_prompt(analysis, answers, persona, lang, seed)
    max_toks_1 = 800 if REC_FAST_MODE else 1200

    try:
        _dbg("calling LLM - round #1")
        raw1 = _chat_with_retry(messages=msgs, max_tokens=max_toks_1, temperature=0.5)
        _dbg(f"round #1 ok, len={len(raw1)}")
    except Exception as e:
        # رسالة تشخيصية واضحة في الكرت الأول
        err = f"❌ خطأ اتصال النموذج: {e}"
        _dbg(f"[LLM] error round #1 -> {e}")
        if _PIPE:
            try:
                _PIPE.send("model_error", {"error": str(e), "job_id": job_id},
                           user_id=user_id, lang=lang, model=CHAT_MODEL)
            except Exception:
                pass
        return [err, "—", "—"]

    # تنظيف المخرجات ثم محاولة القراءة كـ JSON
    raw1 = _strip_code_fence(raw1)
    if not ALLOW_SPORT_NAMES and _contains_blocked_name(raw1):
        raw1 = _mask_names(raw1)
    parsed = _parse_json(raw1) or []
    cleaned = _sanitize_fill(parsed, lang)

    # نقرر هل نحتاج جولة إصلاح
    elapsed = perf_counter() - t0
    time_left = REC_BUDGET_S - elapsed
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}

    mismatch_axes = any(_mismatch_with_axes(rec, axes, lang) for rec in cleaned)
    need_repair_generic = any(
        _too_generic(
            " ".join([_norm_text(c.get("what_it_looks_like","")),
                      _norm_text(c.get("why_you",""))]),
            _MIN_CHARS
        ) for c in cleaned
    )
    missing_fields = any(
        ((_REQUIRE_WIN and not c.get("win_condition"))
         or len(c.get("core_skills") or []) < _MIN_CORE_SKILLS)
        for c in cleaned
    )
    need_repair = (mismatch_axes or need_repair_generic or missing_fields) \
                  and REC_REPAIR_ENABLED and (time_left >= (6 if not REC_FAST_MODE else 4))

    if need_repair:
        exp = _axes_expectations(axes or {}, lang)
        align_hint = ""
        if exp:
            if lang == "العربية":
                align_hint = (
                    "حاذِ التوصيات مع محاور Z:\n"
                    f"- هدوء/أدرينالين: {', '.join(exp.get('calm_adrenaline', []))}\n"
                    f"- فردي/جماعي: {', '.join(exp.get('solo_group', []))}\n"
                    f"- تقني/حدسي: {', '.join(exp.get('tech_intuition', []))}\n"
                )
            else:
                align_hint = (
                    "Align with Z-axes:\n"
                    f"- Calm/Adrenaline: {', '.join(exp.get('calm_adrenaline', []))}\n"
                    f"- Solo/Group: {', '.join(exp.get('solo_group', []))}\n"
                    f"- Technical/Intuitive: {', '.join(exp.get('tech_intuition', []))}\n"
                )
        repair_prompt = {
            "role":"user",
            "content":(
                ("أعد صياغة التوصيات بنبرة إنسانية وواضحة (اسم رياضة مسموح). " if lang=="العربية"
                 else "Rewrite with a warm, human tone (sport names allowed). ")
                + "تأكد من وجود: sport_label, what_it_looks_like, win_condition, 3–5 core_skills, mode, variant_vr, variant_no_vr. "
                + "ممنوع الوقت/التكلفة/العدّات/الجولات/الدقائق/المكان المباشر. "
                + "حسّن محاذاة Z-axes. JSON فقط.\n\n" + align_hint
            )
        }
        try:
            _dbg("calling LLM - round #2 (repair)")
            raw2 = _chat_with_retry(
                messages=msgs + [{"role":"assistant","content":raw1}, repair_prompt],
                max_tokens=(650 if REC_FAST_MODE else 950),
                temperature=0.55
            )
            raw2 = _strip_code_fence(raw2)
            if not ALLOW_SPORT_NAMES and _contains_blocked_name(raw2):
                raw2 = _mask_names(raw2)
            parsed2 = _parse_json(raw2) or []
            cleaned2 = _sanitize_fill(parsed2, lang)

            def score(r: Dict[str,Any]) -> int:
                txt = " ".join([
                    _norm_text(r.get("sport_label","")),
                    _norm_text(r.get("what_it_looks_like","")),
                    _norm_text(r.get("inner_sensation","")),
                    _norm_text(r.get("why_you","")),
                    _norm_text(r.get("first_week","")),
                    _norm_text(r.get("win_condition",""))
                ])
                bonus = 5 * len(r.get("core_skills") or [])
                return len(txt) + bonus

            if sum(map(score, cleaned2)) > sum(map(score, cleaned)):
                cleaned = cleaned2
                _dbg("repair improved result")
        except Exception as e:
            _dbg(f"repair skipped due to error: {e}")

    # فلترة العناوين عالميًا + حفظ في البلاك لِست
    bl = _load_blacklist()
    cleaned = _ensure_unique_labels_v_global(cleaned, lang, bl)
    _persist_blacklist(cleaned, bl)

       # تحويلها لبطاقات نصية
    cards = [_format_card(cleaned[i], i, lang) for i in range(3)]

    # تنظيف أي روابط غير معروفة (حسب الإعدادات)
    try:
        sec = (CFG.get("security") or {})
        if sec.get("scrub_urls", True):
            cards = [scrub_unknown_urls(c, CFG) for c in cards]
    except Exception:
        pass

    # ✅ حارس أخير: تأكد أن كل بطاقة عبارة عن نص (وليس list أو dict)
    try:
        cards = [_norm_text(c) for c in cards]
    except Exception:
        safe_cards: List[str] = []
        for c in cards:
            try:
                safe_cards.append(_norm_text(c))
            except Exception:
                safe_cards.append(str(c))
        cards = safe_cards

    # (اختياري) لوج تشخيصي لو فعّلت REC_DEBUG=1
    _dbg(f"[CARDS TYPES] { [type(c).__name__ for c in cards] }")

    # لوج جودة داخلي (يعتمد على cleaned، مو على cards)
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    quality_flags = {
        "generic": any(_too_generic(
            " ".join([_norm_text(c.get("what_it_looks_like","")),
                      _norm_text(c.get("why_you",""))]),
            _MIN_CHARS) for c in cleaned),
        "low_sensory": any(not _has_sensory(
            " ".join([_norm_text(c.get("what_it_looks_like","")),
                      _norm_text(c.get("inner_sensation",""))])) for c in cleaned),
        "mismatch_axes": any(_mismatch_with_axes(c, axes, lang) for c in cleaned),
        "missing_fields": any(((_REQUIRE_WIN and not c.get("win_condition"))
                               or len(c.get("core_skills") or []) < _MIN_CORE_SKILLS) for c in cleaned)
    }

    try:
        log_user_insight(
            user_id=user_id,
            content={
                "language": lang,
                "answers": {k: v for k, v in (answers or {}).items() if k != "profile"},
                "analysis": analysis,
                "recommendations": cleaned,
                "quality_flags": quality_flags,
                "seed": seed,
                "elapsed_s": round(perf_counter() - t0, 3),
                "fast_mode": REC_FAST_MODE,
                "job_id": job_id
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    try:
        save_cached_recommendation(user_id, answers, lang, cards)
    except Exception:
        pass

    return cards
