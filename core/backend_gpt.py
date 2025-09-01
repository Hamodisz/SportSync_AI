# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
توصيات "هوية رياضية" بثلاث كروت حسّية منظمة + Layer-Z + خطة أسبوع (نوعية فقط) + فكرة VR.
- ممنوع ذكر (الوقت/التكلفة/العدّات/الجولات/الدقائق/المكان المباشر).
- يُسمح بذكر "اسم رياضة/نمط" عند الحاجة لزيادة الوضوح (فكّ الحظر الذكي).
- يحاول مرتين قبل السقوط للـ fallback. يدعم العربية/English.
- يفرض حقول إلزامية لتحويل الغموض إلى رياضة واضحة:
  sport_label, what_it_looks_like, win_condition, core_skills, mode, variant_vr, variant_no_vr
- منع تكرار الهوية منعًا قاطعًا (داخل الجلسة + عالميًا عبر data/blacklist.json) مع فحص تشابه دلالي.
- استيراد Z-intent (تحليل النوايا) مع fallback لغوي إذا تعذر.
- قبل أي توليد: Evidence Gate — لا توصيات بدون أدلة كافية (حل جذري).
- أمان: تنظيف الروابط غير الموثوقة بحسب CFG.security.
- تليمتري: إرسال أحداث إلى DataPipe (Zapier/ملف محلي).
"""

from __future__ import annotations

import os, json, re, hashlib, importlib
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# ========= OpenAI =========
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("أضف الحزمة في requirements: openai>=1.6.1,<2") from e

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OpenAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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

# ========= Paths / Data =========
try:
    HERE = Path(_file_).resolve().parent
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

# ========= Helpers: Arabic normalization =========
_AR_DIAC = r"[ًٌٍَُِّْـ]"
def _normalize_ar(t: str) -> str:
    """تطبيع مبسّط للنص العربي لتحسين المطابقة/المنع."""
    if not t: return ""
    t = re.sub(_AR_DIAC, "", t)
    t = t.replace("أ","ا").replace("إ","ا").replace("آ","ا")
    t = t.replace("ؤ","و").replace("ئ","ي")
    t = t.replace("ة","ه").replace("ى","ي")
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ========= Analysis import (user traits) =========
def _call_analyze_user_from_answers(user_id: str, answers: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """يحاول أكثر من توقيع/مسار لاستيراد تحليل المستخدم."""
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

# ========= Intent (Z-intent) =========
def _call_analyze_intent(answers: Dict[str, Any], lang: str="العربية") -> List[str]:
    """
    يحاول استيراد محلّل نوايا من مشروعك؛ وإلا يستخدم fallback لغوي بسيط.
    """
    for modpath in ("core.layer_z_engine", "analysis.layer_z_engine"):
        try:
            mod = importlib.import_module(modpath)
            if hasattr(mod, "analyze_user_intent"):
                return list(mod.analyze_user_intent(answers, lang=lang) or [])
        except Exception:
            pass

    # Fallback لغوي بسيط
    intents = set()
    blob = " ".join(
        (v["answer"] if isinstance(v, dict) and "answer" in v else str(v))
        for v in (answers or {}).values()
    ).lower()
    blob_ar = _normalize_ar(blob)

    def any_of(words: List[str]) -> bool:
        return any(w in blob or w in blob_ar for w in words)

    if any_of(["vr","واقع افتراضي","نظاره","افتراضي"]): intents.add("VR")
    if any_of(["تكتيك","تكتيكي","tactic","ambush","كمين"]): intents.add("تكتيكي")
    if any_of(["قتال","مبارزه","اشتباك","combat"]): intents.add("قتالي")
    if any_of(["هدوء","تنفس","تنفّس","تركيز","صفاء","calm","breath"]): intents.add("هدوء/تنفّس")
    if any_of(["سرعه","اندفاع","أدرينالين","انقضاض","strike","fast"]): intents.add("أدرينالين")
    if any_of(["فردي","لوحدي","solo","وحيد"]): intents.add("فردي")
    if any_of(["فريق","جماعي","team","group"]): intents.add("جماعي")
    if any_of(["لغز","الغاز","puzzle","خدعه بصريه"]): intents.add("ألغاز/خداع")
    if any_of(["دقه","تصويب","نشان","precision","mark"]): intents.add("دقة/تصويب")
    if any_of(["تخفي","stealth","ظل"]): intents.add("تخفّي")
    if any_of(["توازن","قبضه","grip","balance","تسلق","climb"]): intents.add("قبضة/توازن")
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
    """تقييم أدلة بسيط إذا لم يتوفر core/evidence_gate.py."""
    if not isinstance(answers, dict) or not answers:
        status = "fail"
        total_chars = 0
        answered = 0
    else:
        vals = [_norm_answer_value(v) for v in answers.values() if str(v).strip()]
        total_chars = sum(len(s.strip()) for s in vals)
        answered = sum(1 for s in vals if len(s.strip()) >= 3)

        # required keys إن وُجدت
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

    # followups (قصيرة ومباشرة)
    if lang == "العربية":
        followups = [
            "تفضّل اللعب: فردي أم جماعي؟ ولماذا بش一句.",
            "تميل لهدوء وانسياب أم أدرينالين وقرارات خاطفة؟",
            "هل تحب دقّة/تصويب أم ألغاز/خداع بصري أثناء الحركة؟"
        ]
    else:
        followups = [
            "Do you prefer solo or team play — and why, in one short line?",
            "Do you want calm/flow or adrenaline/snap decisions?",
            "Are you more into precision/aim or puzzles/visual feints in motion?"
        ]

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

# أسماء/أنماط عامة نمنعها لأنها ركيكة
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

def _answers_to_bullets(answers: Dict[str, Any]) -> str:
    out = []
    for k, v in (answers or {}).items():
        if k == "profile":
            continue
        if isinstance(v, dict):
            q, a = v.get("question", k), v.get("answer", "")
        else:
            q, a = str(k), v
        if isinstance(a, list):
            a = ", ".join(map(str, a))
        out.append(f"- {q}: {a}")
    return "\n".join(out)

def _too_generic(text: str, min_chars: int = 280) -> bool:
    t = (text or "").strip()
    return len(t) < min_chars or any(p in t for p in _AVOID_GENERIC)

def _has_sensory(text: str, min_hits: int = 3) -> bool:
    return sum(1 for w in _SENSORY if w in (text or "")) >= min_hits

def _is_meaningful(rec: Dict[str, Any]) -> bool:
    blob = " ".join([
        rec.get("sport_label",""), rec.get("what_it_looks_like",""),
        rec.get("why_you",""), rec.get("first_week",""),
        rec.get("progress_markers",""), rec.get("win_condition","")
    ]).strip()
    return len(blob) >= 120

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
    blob = " ".join(str(rec.get(k,"")) for k in ("what_it_looks_like","inner_sensation","why_you","first_week"))
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
    for k in ("sport_label","scene","what_it_looks_like","inner_sensation","why_you",
              "first_week","progress_markers","win_condition","core_skills","variant_vr","variant_no_vr","vr_idea","mode"):
        if isinstance(r.get(k), str):
            r[k] = _scrub_forbidden(_mask_names(r[k].strip()))
    if isinstance(r.get("core_skills"), str):
        parts = [p.strip(" -•\t") for p in re.split(r"[,\n،]+", r["core_skills"]) if p.strip()]
        r["core_skills"] = parts[:6]
    if not isinstance(r.get("core_skills"), list):
        r["core_skills"] = []
    try:
        d = int(r.get("difficulty", 3))
        r["difficulty"] = max(1, min(5, d))
    except Exception:
        r["difficulty"] = 3
    if r.get("mode") not in ("Solo","Team","Solo/Team","فردي","جماعي","فردي/جماعي"):
        r["mode"] = r.get("mode","Solo")
    return r

def _fallback_identity(i: int, lang: str) -> Dict[str, Any]:
    """فولباك قوي يعطي رياضة واضحة بدون أرقام/أماكن."""
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
                "variant_no_vر":"عناصر قبضة آمنة خفيفة.",
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
            r = pick_unique_fallback(i)
            lab = _canonical_label(r.get("sport_label",""))

        if lab in used_labels:
            r = pick_unique_fallback(i)
            lab = _canonical_label(r.get("sport_label",""))

        sig = _sig_for_rec(r)
        if any(_jaccard(sig, s) > 0.6 for s in used_sigs):
            r = pick_unique_fallback(i)
            lab = _canonical_label(r.get("sport_label",""))
            sig = _sig_for_rec(r)

        out.append(r)
        used_labels.add(lab)
        used_sigs.append(sig)

    return out

# ========= Prompt Builder =========
def _style_seed(user_id: str, profile: Optional[Dict[str, Any]]) -> int:
    base = user_id or "anon"
    axes = profile.get("axes", {}) if isinstance(profile, dict) else {}
    s = f"{base}:{json.dumps(axes, sort_keys=True, ensure_ascii=False)}"
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                 personality: Any, lang: str, style_seed: int) -> List[Dict[str, str]]:
    bullets = _answers_to_bullets(answers)
    persona = personality if isinstance(personality, str) else json.dumps(personality, ensure_ascii=False)
    profile = analysis.get("encoded_profile") or {}
    axes = profile.get("axes", {})
    exp = _axes_expectations(axes, lang)
    exp_lines = []
    if exp:
        title = {"calm_adrenaline":"هدوء/أدرينالين","solo_group":"فردي/جماعي","tech_intuition":"تقني/حدسي"} \
                if lang=="العربية" else \
                {"calm_adrenaline":"Calm/Adrenaline","solo_group":"Solo/Group","tech_intuition":"Technical/Intuitive"}
        for k, words in exp.items():
            if words:
                exp_lines.append(f"{title[k]}: {', '.join(words)}")
    axis_hint = ("\n".join(exp_lines)) if exp_lines else ""

    # نوايا Z (Intent)
    z_intent = analysis.get("z_intent", [])
    intent_hint = ("، ".join(z_intent) if lang=="العربية" else ", ".join(z_intent)) if z_intent else ""

    if lang == "العربية":
        sys = (
            "أنت مدرّب SportSync AI بنبرة إنسانية لطيفة (صديق محترف).\n"
            "ممنوع ذكر (الوقت/التكلفة/العدّات/الجولات/الدقائق/المكان المباشر).\n"
            "سَمِّ 'هوية/رياضة' واضحة عند الحاجة (مثال: Tactical Immersive Combat).\n"
            "أعِد JSON فقط."
        )
        usr = (
            "حوّل بيانات المستخدم إلى ثلاث توصيات «هوية رياضية واضحة». "
            "أعِد JSON بالمفاتيح: "
            "{\"recommendations\":[{"
            "\"sport_label\":\"...\","
            "\"what_it_looks_like\":\"...\","
            "\"inner_sensation\":\"...\","
            "\"why_you\":\"...\","
            "\"first_week\":\"...\","
            "\"progress_markers\":\"...\","
            "\"win_condition\":\"...\","
            "\"core_skills\":[\"...\",\"...\"],"
            "\"mode\":\"Solo/Team\","
            "\"variant_vr\":\"...\","
            "\"variant_no_vr\":\"...\","
            "\"difficulty\":1-5"
            "}]} "
            "قواعد إلزامية: اذكر win_condition و 3–5 core_skills على الأقل. "
            "حاذِ Z-axes بالكلمات التالية إن أمكن:\n" + axis_hint +
            ("\n\n— نوايا Z المحتملة: " + intent_hint if intent_hint else "") + "\n\n"
            f"— شخصية المدرب:\n{persona}\n\n"
            "— تحليل المستخدم:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— إجابات موجزة:\n" + bullets + "\n\n"
            f"— style_seed: {style_seed}\n"
            "أعِد JSON فقط."
        )
    else:
        sys = (
            "You are a warm, human SportSync coach. "
            "No time/cost/reps/sets/minutes/place. "
            "Name the sport/identity if clarity needs it. Return JSON only."
        )
        usr = (
            "Create THREE clear sport-like identities with required keys: "
            "{\"recommendations\":[{\"sport_label\":\"...\",\"what_it_looks_like\":\"...\",\"inner_sensation\":\"...\","
            "\"why_you\":\"...\",\"first_week\":\"...\",\"progress_markers\":\"...\",\"win_condition\":\"...\","
            "\"core_skills\":[\"...\"],\"mode\":\"Solo/Team\",\"variant_vr\":\"...\",\"variant_no_vr\":\"...\",\"difficulty\":1-5}]} "
            "Align with Z-axes using words:\n" + axis_hint +
            ( "\n\n— Z intents: " + intent_hint if intent_hint else "" ) + "\n\n"
            f"— Coach persona:\n{persona}\n— User analysis:\n" + json.dumps(analysis, ensure_ascii=False) + "\n"
            "— Bulleted answers:\n" + bullets + f"\n— style_seed: {style_seed}\nJSON only."
        )
    return [{"role": "system", "content": sys}, {"role": "user", "content": usr}]

def _parse_json(text: str) -> Optional[List[Dict[str, Any]]]:
    try:
        obj = json.loads(text)
        recs = obj.get("recommendations", [])
        if isinstance(recs, list) and recs:
            return recs
    except Exception:
        pass
    # إصلاح ريجكس: \s وليس "س"
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

def _to_bullets(text: str, max_items: int = 6) -> List[str]:
    if not text: return []
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

    label = (rec.get("sport_label") or "").strip()
    scene = (rec.get("what_it_looks_like") or rec.get("scene") or "").strip()
    inner = (rec.get("inner_sensation") or "").strip()
    why   = (rec.get("why_you") or "").strip()
    week  = _to_bullets(rec.get("first_week") or "")
    prog  = _to_bullets(rec.get("progress_markers") or "", max_items=4)
    win   = (rec.get("win_condition") or "").strip()
    skills= rec.get("core_skills") or []
    diff  = rec.get("difficulty", 3)
    mode  = (rec.get("mode") or "Solo").strip()
    vr    = (rec.get("variant_vr") or rec.get("vr_idea") or "").strip()
    novr  = (rec.get("variant_no_vr") or "").strip()

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
            for s in skills[:5]: out.append(f"- {s}")
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
    temp: List[Dict[str, Any]] = []
    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        r = _fill_defaults(_sanitize_record(r), lang)
        blob = " ".join([
            r.get("sport_label",""), r.get("what_it_looks_like",""),
            r.get("why_you",""), r.get("first_week",""),
            r.get("progress_markers",""), r.get("win_condition","")
        ])
        if _too_generic(blob, _MIN_CHARS) or not _has_sensory(blob) or not _is_meaningful(r) \
           or (_REQUIRE_WIN and not r.get("win_condition")) \
           or len(r.get("core_skills") or []) < _MIN_CORE_SKILLS \
           or _label_is_generic(r.get("sport_label","")):
            r = _fallback_identity(i, lang)
        temp.append(r)
    return _hard_dedupe_and_fill(temp, lang)

# ====== Blacklist (persistent, JSON) =========================================
def _load_blacklist() -> dict:
    bl = _load_json_safe(BL_PATH)
    if not isinstance(bl.get("labels"), dict):
        bl["labels"] = {}
    bl.setdefault("version", "1.0")
    return bl

# — aliases/canonicalization helpers
KB = _load_json_safe(KB_PATH)
_ALIAS_MAP = {}
if isinstance(KB.get("label_aliases"), dict):
    for canon, alist in KB["label_aliases"].items():
        for a in alist:
            _ALIAS_MAP[_normalize_ar(a).lower()] = canon
AL2 = _load_json_safe(AL_PATH)
if isinstance(AL2.get("canonical"), dict):
    for a, canon in AL2["canonical"].items():
        _ALIAS_MAP[_normalize_ar(a).lower()] = canon

_FORBIDDEN_GENERIC = set(
    KB.get("guards", {}).get("forbidden_generic_labels", [])
) | set(AL2.get("forbidden_generic", []) or [])

def _canon_label(label: str) -> str:
    lab = _normalize_ar(label or "").lower().strip(" -—:،")
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
    for i, r in enumerate(recs):
        r = dict(r or {})
        label = r.get("sport_label") or ""
        if _is_forbidden_generic(label) or not label.strip():
            hint = "تكتيكي تخفّي" if lang == "العربية" else "Tactical Stealth"
            label = hint
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

# ========= PUBLIC API =========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية", user_id: str = "N/A") -> List[str]:
    # Evidence Gate أولًا — لا توصيات بدون أدلة كافية
    eg = _run_egate(answers or {}, lang=lang)
    if _PIPE:
        try:
            _PIPE.send(
                event_type="egate_decision",
                payload={"status": eg.get("status"), "answered": eg.get("answered"), "total_chars": eg.get("total_chars"),
                         "required_missing": eg.get("required_missing", [])},
                user_id=user_id, lang=("العربية" if lang=="العربية" else "English"),
                model=CHAT_MODEL
            )
        except Exception:
            pass

    if eg.get("status") != "pass":
        # نرجع بطاقة أسئلة متابعة فقط (بدون توصيات)
        card = _format_followup_card(eg.get("followup_questions", []), lang=lang)
        # فلترة روابط (لو أي نص فيه روابط)
        card = scrub_unknown_urls(card, CFG)
        return [card, "—", "—"]

    if OpenAI_CLIENT is None:
        return ["❌ OPENAI_API_KEY غير مضبوط في خدمة الـ Quiz.", "—", "—"]

    # تحليل المستخدم + طبقة Z + Intent
    analysis = _call_analyze_user_from_answers(user_id, answers, lang)

    silent = []
    try:
        silent = analyze_silent_drivers(answers, lang=lang) or []
    except Exception:
        pass
    analysis["silent_drivers"] = silent

    try:
        z_intent = _call_analyze_intent(answers, lang=lang)
    except Exception:
        z_intent = []
    if z_intent:
        analysis["z_intent"] = z_intent

    # بروفايل مُرمّز (إن وُجد)
    profile = _extract_profile(answers, lang)
    if profile:
        analysis["encoded_profile"] = profile
        if "axes" in profile: analysis["z_axes"] = profile["axes"]
        if "scores" in profile: analysis["z_scores"] = profile["scores"]

    # شخصية المدرب من الكاش
    persona = get_cached_personality(analysis, lang=lang)
    if not persona:
        persona = {"name":"SportSync Coach","tone":"حازم-هادئ","style":"حسّي واقعي إنساني","philosophy":"هوية حركة بلا أسماء مع وضوح هويّة"}
        try:
            save_cached_personality(analysis, persona, lang=lang)
        except Exception:
            pass

    # === أول محاولة
    seed = _style_seed(user_id, profile or {})
    msgs = _json_prompt(analysis, answers, persona, lang, seed)
    try:
        resp = OpenAI_CLIENT.chat.completions.create(
            model=CHAT_MODEL,
            messages=msgs,
            temperature=0.5,           # ↓ ثبات أعلى
            top_p=0.9,
            presence_penalty=0.15,
            frequency_penalty=0.1,
            max_tokens=1400
        )
        raw1 = (resp.choices[0].message.content or "").strip()
        print(f"[AI] model={CHAT_MODEL} len={len(raw1)} raw[:140]={raw1[:140]!r}")
    except Exception as e:
        err = f"❌ خطأ اتصال النموذج: {e}"
        if _PIPE:
            try:
                _PIPE.send("model_error", {"error": str(e)}, user_id=user_id, lang=lang, model=CHAT_MODEL)
            except Exception:
                pass
        return [err, "—", "—"]

    # Parsing + Sanitize
    if not ALLOW_SPORT_NAMES and _contains_blocked_name(raw1):
        raw1 = _mask_names(raw1)
    parsed = _parse_json(raw1) or []
    cleaned = _sanitize_fill(parsed, lang)

    # ===== محاذاة Z-axes + إصلاح ثانٍ إذا لزم =====
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    mismatch_axes = any(_mismatch_with_axes(rec, axes, lang) for rec in cleaned)
    need_repair_generic = any(_too_generic(" ".join([c.get("what_it_looks_like",""), c.get("why_you","")]), _MIN_CHARS) for c in cleaned)
    missing_fields = any(((_REQUIRE_WIN and not c.get("win_condition")) or len(c.get("core_skills") or []) < _MIN_CORE_SKILLS) for c in cleaned)
    need_repair = mismatch_axes or need_repair_generic or missing_fields

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
                 else "Rewrite with a warm, human tone (sport names allowed). ") +
                "تأكد من وجود: sport_label, what_it_looks_like, win_condition, 3–5 core_skills, mode, variant_vr, variant_no_vr. "
                "ممنوع الوقت/التكلفة/العدّات/الجولات/الدقائق/المكان المباشر. "
                "حسّن محاذاة Z-axes. JSON فقط.\n\n" + align_hint
            )
        }
        try:
            resp2 = OpenAI_CLIENT.chat.completions.create(
                model=CHAT_MODEL,
                messages=msgs + [{"role":"assistant","content":raw1}, repair_prompt],
                temperature=0.55,
                top_p=0.9,
                presence_penalty=0.15,
                frequency_penalty=0.1,
                max_tokens=1400
            )
            raw2 = (resp2.choices[0].message.content or "").strip()
            if not ALLOW_SPORT_NAMES and _contains_blocked_name(raw2):
                raw2 = _mask_names(raw2)
            parsed2 = _parse_json(raw2) or []
            cleaned2 = _sanitize_fill(parsed2, lang)

            def score(r: Dict[str,Any]) -> int:
                txt = " ".join([
                    r.get("sport_label",""), r.get("what_it_looks_like",""),
                    r.get("inner_sensation",""), r.get("why_you",""),
                    r.get("first_week",""), r.get("win_condition","")
                ])
                bonus = 5*len(r.get("core_skills") or [])
                return len(txt) + bonus

            if sum(map(score, cleaned2)) > sum(map(score, cleaned)):
                cleaned = cleaned2
        except Exception:
            pass

    # ===== تأكيد عدم التكرار عالميًا + تسجيل في البلاك ليست =====
    bl = _load_blacklist()
    cleaned = _ensure_unique_labels_v_global(cleaned, lang, bl)
    _persist_blacklist(cleaned, bl)

    # بناء الكروت
    cards = [_format_card(cleaned[i], i, lang) for i in range(3)]

    # أمان الروابط بحسب CFG.security
    try:
        cards = [scrub_unknown_urls(c, CFG) for c in cards]
    except Exception:
        pass

    # لوق مع أعلام الجودة + تليمتري
    quality_flags = {
        "generic": any(_too_generic(" ".join([c.get("what_it_looks_like",""), c.get("why_you","")]), _MIN_CHARS) for c in cleaned),
        "low_sensory": any(not _has_sensory(" ".join([c.get("what_it_looks_like",""), c.get("inner_sensation","")])) for c in cleaned),
        "mismatch_axes": any(_mismatch_with_axes(c, axes, lang) for c in cleaned),
        "missing_fields": any(((_REQUIRE_WIN and not c.get("win_condition")) or len(c.get("core_skills") or []) < _MIN_CORE_SKILLS) for c in cleaned)
    }

    try:
        log_user_insight(
            user_id=user_id,
            content={
                "language": lang,
                "answers": {k: v for k, v in (answers or {}).items() if k != "profile"},
                "analysis": analysis,
                "silent_drivers": silent,
                "encoded_profile": profile,
                "recommendations": cleaned,
                "quality_flags": quality_flags,
                "seed": seed
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    if _PIPE:
        try:
            _PIPE.send(
                event_type="recommendation_emitted",
                payload={"quality_flags": quality_flags, "labels": [c.get("sport_label","") for c in cleaned]},
                user_id=user_id, lang=("العربية" if lang=="العربية" else "English"),
                model=CHAT_MODEL
            )
        except Exception:
            pass

    return cards
