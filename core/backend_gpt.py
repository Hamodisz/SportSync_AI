# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
توصيات "هوية رياضية بلا أسماء" بثلاث كروت حسّية + محاذاة Z-axes + خطة نوعية + فكرة VR.
- لا وقت/مكان/تكلفة/عدّات/جولات (نحذف الجملة المخالفة بالكامل).
- مسموح تسمية الهوية/اللعبة عند الحاجة (فك الحظر عن الأسماء بطريقة موجّهة).
- محاولتان لإصلاح الجودة قبل السقوط إلى FallBack ذهبي.
- يدعم العربية/English.
"""

from _future_ import annotations

import os, json, re
from typing import Any, Dict, List, Optional

# ========= OpenAI =========
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("أضف الحزمة في requirements: openai>=1.6.1,<2") from e

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OpenAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")  # بدّل إلى gpt-4o-mini لتكلفة أقل

# ========= Project imports (with safe fallbacks) =========
try:
    from core.user_logger import log_user_insight
except Exception:
    def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "event") -> None:
        print(f"[LOG:{event_type}] {user_id}: {list(content.keys())}")

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
    from core.user_analysis import analyze_user_from_answers
except Exception:
    def analyze_user_from_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
        return {"quick_profile": "fallback", "raw_answers": answers}

# Layer Z قد تكون عندك في core أو analysis
try:
    from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    try:
        from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
    except Exception:
        def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
            return ["إنجازات قصيرة", "نفور من التكرار", "تفضيل تحدّي ذهني"]

# ========= إعدادات النص/الجودة =========
_ALLOW_SPORT_NAMES = True  # فك الحظر عن الأسماء عند الحاجة (اسم الهوية/أمثلة ألعاب)

_AVOID_GENERIC = [
    "أي نشاط بدني مفيد","اختر ما يناسبك","ابدأ بأي شيء","جرّب أكثر من خيار",
    "لا يهم النوع","تحرك فقط","نشاط عام","رياضة عامة","أنت تعرف ما يناسبك"
]
_SENSORY = [
    "تنفّس","إيقاع","توتر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","امتداد","حرق لطيف","صفاء","تماسك","اندفاع","تمويه","كمين"
]
_TACTICAL_AR = [
    "كمين","مراوغة","اختباء","انقضاض","تضليل","تمويه","مسح محيطي",
    "قفل هدف","انسحاب تكتيكي","تشتيت","إسناد","استدراج","تحييد"
]
_TACTICAL_EN = [
    "ambush","dodge","evade","stealth","flank","lure","decoy","pounce",
    "lock-on","scan","disengage","feint","neutralize","cover","support"
]

# كلمات/أنماط محظورة (أرقام زمن/عدّات/تكلفة/مكان مباشر)
_FORBIDDEN_SENT = re.compile(
    r"(\b\d+(\.\d+)?\s*(?:min|mins|minute|minutes|second|seconds|hour|hours|دقيقة|دقائق|ثانية|ثواني|ساعة|ساعات)\b|"
    r"(?:rep|reps|set|sets|تكرار|عدة|عدات|جولة|جولات|×)|"
    r"(?:تكلفة|ميزانية|cost|budget|ريال|دولار|\$|€)|"
    r"(?:بالبيت|في\s*البيت|قرب\s*المنزل|بالمنزل|في\s*النادي|في\s*الجيم|صالة|نادي|جيم|غرفة|ساحة|ملعب|حديقة|شاطئ|"
    r"طبيعة|خارجي(?:ة)?|داخل(?:ي|ية)?|outdoor|indoor|park|beach|gym|studio))",
    re.IGNORECASE
)

def _split_sentences(text: str) -> List[str]:
    if not text: return []
    return [s.strip() for s in re.split(r"(?<=[\.\!\?؟])\s+|[\n،]+", text) if s.strip()]

def _scrub_forbidden(text: str) -> str:
    """يحذف أي جملة تتضمن مكان/زمن/تكلفة/عدّات/جولات بالكامل."""
    kept = [s for s in _split_sentences(text) if not _FORBIDDEN_SENT.search(s)]
    return "، ".join(kept).strip(" .،-")

def _answers_to_bullets(answers: Dict[str, Any]) -> str:
    out = []
    for k, v in (answers or {}).items():
        if k == "profile":
            continue
        if isinstance(v, dict):
            q, a = v.get("question", k), v.get("answer", "")
        else:
            q, a = str(k), v
        if isinstance(a, list): a = ", ".join(map(str, a))
        out.append(f"- {q}: {a}")
    return "\n".join(out)

def _too_generic(text: str, min_chars: int = 260) -> bool:
    t = (text or "").strip()
    return len(t) < min_chars or any(p in t for p in _AVOID_GENERIC)

def _has_sensory(text: str, min_hits: int = 4) -> bool:
    return sum(1 for w in _SENSORY if w in (text or "")) >= min_hits

def _count_tactical(text: str, lang: str) -> int:
    lst = _TACTICAL_AR if lang == "العربية" else _TACTICAL_EN
    low = (text or "").lower()
    return sum(1 for w in lst if w.lower() in low)

# ========= Z-axes alignment =========
_AR_TOK = {
    "calm": ["هدوء","تنفّس","سكون","صفاء","بطيء"],
    "adren": ["اندفاع","سريع","اشتباك","قوة لحظية","حسم"],
    "solo": ["فردي","لوحدك","ذاتية"],
    "group": ["مع ناس","جماعة","شريك","فريق"],
    "tech": ["تقنية","تفاصيل","إتقان","ضبط"],
    "intu": ["حدس","تلقائي","على الإحساس","بديهة"]
}
_EN_TOK = {
    "calm": ["calm","slow","breath","quiet","settle"],
    "adren": ["fast","burst","risk","adrenaline","clutch"],
    "solo": ["solo","alone","by yourself"],
    "group": ["with people","partner","team","group"],
    "tech": ["technique","detail","precise","drill"],
    "intu": ["by feel","intuitive","go with it"]
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

def _mismatch_with_axes(text: str, axes: Dict[str, float], lang: str) -> bool:
    exp = _axes_expectations(axes or {}, lang)
    if not exp: return False
    low = (text or "").lower()
    for words in exp.values():
        if words and not any(w.lower() in low for w in words):
            return True
    return False

# ========= Fallbacks الذهبية (نفس الجودة المرجعية) =========
def _golden_fallbacks(lang: str) -> List[Dict[str, Any]]:
    if lang == "العربية":
        return [
            {
                "identity_title": "Tactical Immersive Combat",
                "what_is_it": [
                    "مهمّات تكتيكية بقراءة خصم وتمويه وكمين وانقضاض",
                    "أدرينالين محسوب: تلتقط إشارات وتقفل هدف وتبدّل الخطة في لحظة",
                    "ممكن عبر منصّات VR تكتيكية أو محاكيات ميدان افتراضي"
                ],
                "why_you": "تكره الرتابة وتنجذب للتحدّي الذهني الخالي من الثرثرة — تحب الهيمنة الهادئة: تفهم، تحاصر، ثم تحسم.",
                "real_world_shape": [
                    "سيناريو تسلّل: مسح محيطي، مسار آمن، تضليل ثم حسم نظيف",
                    "تتبّع النفس والنبض والاستجابة للصوت/الظل بسرعة هادئة",
                    "كل جولة بأسلوب مختلف (مراوغة/استدراج/تحييد)"
                ],
                "notes": ["اعتبرها تدريب ذكاء تحت ضغط لا رياضة تقليدية.", "لو زاد الاندفاع، ارجع لمسح أبطأ ثم حسم واضح."],
                "expansions": ["نسخة Solo لرفع الحدس والردّ السريع", "نسخة Team لإسناد وتوزيع أدوار"],
                "difficulty": 3,
                "vr_idea": "ساحة مهمّات تكتيكية بمحفّزات صوت/ظل."
            },
            {
                "identity_title": "Stealth-Flow Missions",
                "what_is_it": [
                    "انسياب هادئ مع قرارات صامتة وتمويه بصري",
                    "تحكم بالتنفس لتبريد الأدرينالين وبناء حضور ذهني",
                    "مهام قصيرة بتغيرات سطح/إيقاع بدون تكرار"
                ],
                "why_you": "تبحث عن تقدّم محسوس من غير ضجيج وتحب السيطرة الداخلية مع بصمة تكتيكية.",
                "real_world_shape": [
                    "تتبُّع مسارات ظلّ، تبديل زوايا، تجميد لحظة الحسم",
                    "ترميز إشارات سمعية/بصرية ثم قرار حدسي محسوب",
                    "انسحاب تكتيكي إذا اختل الإيقاع ثم إعادة تموضع"
                ],
                "notes": ["حافظ على شريط تنفس مستقر أثناء القرار.", "دوّن نمط القرارات التي تعطيك صفاء."],
                "expansions": ["دمج طبيعة افتراضية + مهام صامتة", "Puzzle-Hunt مع أهداف متغيرة"],
                "difficulty": 2,
                "vr_idea": "VR خفيف يبرز الإيقاع والتتبّع."
            },
            {
                "identity_title": "Mind-Trap Puzzles in Motion",
                "what_is_it": [
                    "ألغاز قرار تحت حركة: تفكّر وتتحرّك في آنٍ واحد",
                    "إقفال مسارات، فتح اختصارات، وخدع بصرية بسيطة",
                    "تدرّب على الانتقال بين حدس سريع وتحليل دقيق"
                ],
                "why_you": "تحب الفهم العميق وإثبات التفوّق الهادئ على المسار لا على الناس.",
                "real_world_shape": [
                    "سلسلة مصائد ذهنية متحركة: تختار، تختبر، ثم تصحّح",
                    "إيقاع متنقّل بين تركيز دقيق وتدفّق تلقائي",
                    "تقييم بعدي قصير: ما الذي حُسم بسرعة؟"
                ],
                "notes": ["لا تتعجّل الحسم: دقّة قبل سرعة.", "اسمح للهفوة الواحدة أن تعلّمك مسارًا أفضل."],
                "expansions": ["Solo تحليلي أو Team لتوزيع الأدوار الذهنية", "هجين AI يولّد ألغازًا على مزاجك"],
                "difficulty": 2,
                "vr_idea": "غرف ألغاز تفاعلية متبدلة."
            }
        ]
    else:
        return [
            {
                "identity_title": "Tactical Immersive Combat",
                "what_is_it": [
                    "Stealth missions with decoy, ambush and clean pounce",
                    "Measured adrenaline: scan, lock-on, pivot plan instantly",
                    "Runs on tactical VR platforms or simulated arenas"
                ],
                "why_you": "You reject fluff and crave quiet dominance: understand, trap, then finish.",
                "real_world_shape": [
                    "Stealth entry → area scan → safe path → feint → decisive strike",
                    "Breath/HR tracking, rapid calm responses to sound/shadow",
                    "Each round a new pattern (evade/lure/neutralize)"
                ],
                "notes": ["Treat it as ‘intelligence under pressure’ not a classic sport.", "Slow scan if arousal spikes, then clean finish."],
                "expansions": ["Solo for instincts, Team for roles and cover", "Nature-VR hybrid for nervous-system balance"],
                "difficulty": 3,
                "vr_idea": "Tactical mission arena with sound/lighting cues."
            },
            # (…الثاني والثالث نفس المعاني بالإنجليزية إن احتجت)
        ]

# ========= Prompt (JSON schema جديد) =========
def _json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                 personality: Any, lang: str) -> List[Dict[str, str]]:
    bullets = _answers_to_bullets(answers)
    persona = personality if isinstance(personality, str) else json.dumps(personality, ensure_ascii=False)

    profile = analysis.get("encoded_profile") or {}
    axes = profile.get("axes", analysis.get("z_axes", {})) or {}
    axes_str = json.dumps(axes, ensure_ascii=False)

    if lang == "العربية":
        sys = (
            "أنت مدرّب SportSync AI بنبرة إنسانية دافئة (صديق محترف). "
            "ممنوع ذكر الوقت/المكان/التكلفة/العدّات/الجولات أو أرقام الدقائق. "
            "مسموح تسمية الهوية أو ذكر مثال لعبة/أسلوب عند الحاجة. "
            "استخدم لغة حسّية وتكتيكية بأفعال قوية وبجمل قصيرة. "
            "أعد JSON فقط."
        )
        usr = (
            "أعد ثلاث توصيات «هوية حركة» بجودة عالية وفق المخطط التالي:\n"
            "{\"recommendations\":[{\n"
            "  \"identity_title\":\"اسم الهوية واضح غير عام (مثال مسموح: Tactical Immersive Combat)\",\n"
            "  \"what_is_it\":\"3-5 نقاط حسّية تصف التجربة (عناصر لعب/قرارات/آليات)\",\n"
            "  \"why_you\":\"3 نقاط تربط الدوافع الداخلية/Layer-Z مباشرة (مثال: تكره الرتابة، هيمنة هادئة)\",\n"
            "  \"real_world_shape\":\"3 نقاط كيف تبدو الجلسة فعليًا دون وقت/مكان/تكلفة/عدّات\",\n"
            "  \"notes\":\"2-3 ملاحظات ذكية\",\n"
            "  \"expansions\":\"2 توسعات (Solo/Team أو هجين AI/طبيعة)\",\n"
            "  \"difficulty\":1-5,\n"
            "  \"vr_idea\":\"إن وُجد\"\n"
            "}]} \n"
            "التزم بمفردات حسّية وتكتيكية (كمين، مراوغة، تمويه، انقضاض، مسح محيطي، قفل هدف...).\n"
            f"— شخصية المدرب: {persona}\n"
            f"— محاور Z-axes: {axes_str}\n"
            "— إجابات المستخدم:\n" + bullets + "\n"
            "أعد JSON فقط بلا أي شرح خارجي."
        )
    else:
        sys = (
            "You are a warm, human SportSync coach. "
            "Forbid time/place/cost/reps/sets; allow naming the identity or example games when helpful. "
            "Use sensory and tactical verbs; short sentences. Return JSON only."
        )
        usr = (
            "Produce THREE movement-identity suggestions with this schema:\n"
            "{\"recommendations\":[{\"identity_title\":\"...\",\"what_is_it\":\"3-5 bullets\","
            "\"why_you\":\"3 bullets tied to Layer-Z\",\"real_world_shape\":\"3 bullets\","
            "\"notes\":\"2-3 bullets\",\"expansions\":\"2 options\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            f"— Coach persona: {persona}\n"
            f"— Z-axes: {axes_str}\n"
            "— User answers:\n" + bullets + "\n"
            "Return JSON only."
        )
    return [{"role": "system", "content": sys}, {"role": "user", "content": usr}]

# ========= JSON parsing =========
def _parse_json(text: str) -> Optional[List[Dict[str, Any]]]:
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

# ========= Sanitization + Quality =========
def _listify(x: Any) -> List[str]:
    if not x: return []
    if isinstance(x, list): return [str(i) for i in x if str(i).strip()]
    return [s.strip() for s in re.split(r"[;\n\.•]+", str(x)) if s.strip()]

def _sanitize_record(r: Dict[str, Any]) -> Dict[str, Any]:
    """ينظّف الحقول من الجُمل المخالفة، ويسوّي الأنواع (list/str)."""
    r = dict(r or {})
    for key in ("identity_title","why_you","vr_idea"):
        if isinstance(r.get(key), str):
            r[key] = _scrub_forbidden(r[key])
    for key in ("what_is_it","real_world_shape","notes","expansions"):
        if key in r:
            joined = "، ".join(_listify(r.get(key)))
            r[key] = _listify(_scrub_forbidden(joined))
    try:
        d = int(r.get("difficulty", 3))
        r["difficulty"] = max(1, min(5, d))
    except Exception:
        r["difficulty"] = 3
    return r

def _score_quality(rec: Dict[str, Any], axes: Dict[str, float], lang: str) -> Dict[str, Any]:
    text_blob = " ".join([
        str(rec.get("identity_title","")),
        " ".join(rec.get("what_is_it",[]) or _listify(rec.get("what_is_it"))),
        str(rec.get("why_you","")),
        " ".join(rec.get("real_world_shape",[]) or _listify(rec.get("real_world_shape"))),
        " ".join(rec.get("notes",[]) or _listify(rec.get("notes"))),
        " ".join(rec.get("expansions",[]) or _listify(rec.get("expansions")))
    ])
    tactical = _count_tactical(text_blob, lang)
    sensory  = _has_sensory(text_blob, 4)
    titled   = len((rec.get("identity_title") or "").strip()) >= 4
    generic  = _too_generic(text_blob, 240)
    mismatch = _mismatch_with_axes(text_blob, axes, lang)
    forbidden = bool(_FORBIDDEN_SENT.search(text_blob))

    score = (tactical >= 2) + sensory + titled + (not generic) + (not mismatch) + (not forbidden)
    return {
        "score": int(score),
        "flags": {
            "tactical_ok": tactical >= 2,
            "sensory_ok": sensory,
            "title_ok": titled,
            "generic": generic,
            "mismatch_axes": mismatch,
            "forbidden": forbidden
        }
    }

def _quality_gate_and_fill(recs: List[Dict[str, Any]], lang: str, axes: Dict[str, float]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    gold = _golden_fallbacks(lang)
    gi = 0
    for i in range(3):
        r = _sanitize_record(recs[i] if i < len(recs) else {})
        q = _score_quality(r, axes, lang)
        if q["score"] < 5:  # عتبة صارمة
            r = gold[gi % len(gold)]
            gi += 1
        out.append(_sanitize_record(r))
    return out

# ========= Formatting (كروت نصّية جاهزة) =========
def _to_bullets(text: Any, max_items: int = 6) -> List[str]:
    return _listify(text)[:max_items]

def _format_card(rec: Dict[str, Any], idx: int, lang: str) -> str:
    title = rec.get("identity_title", "").strip()
    what  = _to_bullets(rec.get("what_is_it"))
    why   = _to_bullets(rec.get("why_you"))
    real  = _to_bullets(rec.get("real_world_shape"))
    notes = _to_bullets(rec.get("notes"))
    exp   = _to_bullets(rec.get("expansions"), max_items=3)
    diff  = rec.get("difficulty", 3)
    vr    = (rec.get("vr_idea") or "").strip()

    if lang == "العربية":
        out = []
        out.append(f"🎯 الهوية المثالية لك: {title if title else f'الخيار {idx+1}'}")
        out.append("")
        out.append("💡 ما هي؟")
        for b in what: out.append(f"\t• {b}")
        out.append("")
        out.append("🎮 ليه تناسبك؟")
        for b in why: out.append(f"\t• {b}")
        out.append("")
        out.append("🔍 شكلها الواقعي:")
        for b in real: out.append(f"\t• {b}")
        if notes:
            out.append("\n👁‍🗨 ملاحظات مهمة:")
            for b in notes: out.append(f"\t• {b}")
        if exp:
            out.append("\n⸻\n🧩 توسعة:")
            for b in exp: out.append(f"\t• {b}")
        out.append(f"\nالمستوى التقريبي: {diff}/5" + (f" — VR: {vr}" if vr else ""))
        return "\n".join(out).strip()
    else:
        out = []
        out.append(f"🎯 Best-fit identity: {title if title else f'Option {idx+1}'}\n")
        out.append("💡 What is it?")
        for b in what: out.append(f"\t• {b}")
        out.append("\n🎮 Why you?")
        for b in why: out.append(f"\t• {b}")
        out.append("\n🔍 Real-world shape:")
        for b in real: out.append(f"\t• {b}")
        if notes:
            out.append("\n👁‍🗨 Notes:")
            for b in notes: out.append(f"\t• {b}")
        if exp:
            out.append("\n🧩 Expansions:")
            for b in exp: out.append(f"\t• {b}")
        out.append(f"\nApprox difficulty: {diff}/5" + (f" — VR: {vr}" if vr else ""))
        return "\n".join(out).strip()

# ========= PUBLIC API =========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية", user_id: str = "N/A") -> List[str]:
    if OpenAI_CLIENT is None:
        return ["❌ OPENAI_API_KEY غير مضبوط في خدمة الـ Quiz.", "—", "—"]

    # تحليل المستخدم + طبقة Z
    analysis = analyze_user_from_answers(answers)
    silent = analyze_silent_drivers(answers, lang=lang) or []
    analysis["silent_drivers"] = silent

    # بروفايل مُشفّر (اختياري)
    profile = None
    try:
        from core.answers_encoder import encode_answers as _enc
        profile = _enc(answers, lang=lang)
    except Exception:
        try:
            from analysis.answers_encoder import encode_answers as _enc2
            profile = _enc2(answers, lang=lang)
        except Exception:
            profile = None

    if profile:
        analysis["encoded_profile"] = profile
        if "axes" in profile: analysis["z_axes"] = profile["axes"]
        if "scores" in profile: analysis["z_scores"] = profile["scores"]

    # شخصية المدرب من الكاش
    persona = get_cached_personality(analysis, lang=lang)
    if not persona:
        persona = {"name":"SportSync Coach","tone":"حازم-هادئ","style":"إنساني حسّي واقعي","philosophy":"هوية حركة بلا أسماء"}
        try:
            save_cached_personality(analysis, persona, lang=lang)
        except Exception:
            pass

    # === محاولة 1
    msgs = _json_prompt(analysis, answers, persona, lang)
    try:
        resp = OpenAI_CLIENT.chat.completions.create(
            model=CHAT_MODEL, messages=msgs, temperature=0.9, max_tokens=1400
        )
        raw1 = (resp.choices[0].message.content or "").strip()
        print(f"[AI] len={len(raw1)} raw[:120]={raw1[:120]!r}")
    except Exception as e:
        # سقوط مباشر للفولباك الذهبي
        cleaned = _golden_fallbacks(lang)[:3]
        return [_format_card(cleaned[i], i, lang) for i in range(3)]

    parsed = _parse_json(raw1) or []
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    cleaned = _quality_gate_and_fill(parsed, lang, axes)

    # === إصلاح موجّه إذا الجودة ضعيفة أو محاذاة Z سيئة
    need_repair = False
    for r in cleaned:
        blob = " ".join([r.get("identity_title","")] + r.get("what_is_it",[]) + r.get("real_world_shape",[]))
        q = _score_quality(r, axes, lang)
        if q["score"] < 5 or _mismatch_with_axes(blob, axes, lang):
            need_repair = True
            break

    if need_repair:
        exp = _axes_expectations(axes, lang)
        align_hint = ""
        if exp:
            if lang == "العربية":
                align_hint = (
                    "حاذِ التوصيات مع محاور Z:\n"
                    f"- كلمات هدوء/أدرينالين: {', '.join(exp.get('calm_adrenaline', []))}\n"
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
            "role": "user",
            "content": (
                ("أعد الصياغة بنبرة إنسانية، أفعال تكتيكية واضحة، واسم هوية قوي عند الحاجة. " if lang=="العربية"
                 else "Rewrite with a warm human tone, clear tactical verbs, and a strong identity title when helpful. ")
                + "احذف أي جملة فيها وقت/مكان/تكلفة/عدّات بالكامل. JSON فقط.\n" + align_hint
            )
        }
        try:
            resp2 = OpenAI_CLIENT.chat.completions.create(
                model=CHAT_MODEL,
                messages=msgs + [{"role":"assistant","content":raw1}, repair_prompt],
                temperature=0.85, max_tokens=1400
            )
            raw2 = (resp2.choices[0].message.content or "").strip()
            parsed2 = _parse_json(raw2) or []
            cleaned2 = _quality_gate_and_fill(parsed2, lang, axes)

            # اختر الأحسن عبر مجموع نقاط الجودة
            def total_score(lst: List[Dict[str,Any]]) -> int:
                return sum(_score_quality(r, axes, lang)["score"] for r in lst)
            if total_score(cleaned2) >= total_score(cleaned):
                cleaned = cleaned2
        except Exception:
            pass

    cards = [_format_card(cleaned[i], i, lang) for i in range(3)]

    # لوق مختصر
    try:
        log_user_insight(
            user_id=user_id,
            content={
                "language": lang,
                "answers": {k: v for k, v in answers.items() if k != "profile"},
                "analysis": analysis,
                "silent_drivers": silent,
                "encoded_profile": profile,
                "recommendations_json": cleaned,
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    return cards
