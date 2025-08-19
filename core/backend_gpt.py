# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
توصيات "هوية رياضية بلا أسماء" بثلاث كروت حسّية منظمة + طبقة Z + خطة أسبوع (نوعية فقط) + فكرة VR.
- لا مكان/زمن/تكلفة ولا عدّات/جولات/دقائق في الإخراج.
- يحاول مرتين قبل السقوط للـ fallback. يدعم العربية/English.
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
if not OPENAI_API_KEY:
    OpenAI_CLIENT = None
else:
    OpenAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

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

# ========= (جديد) مُشفِّر الإجابات (اختياري) =========
def _extract_profile(answers: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    """
    يعيد بروفايل مُشفَّر إن وُجد في answers تحت المفتاح "profile"،
    أو يحاول توليده عبر core.answers_encoder.encode_answers (إن توفّر).
    يُرجِع None لو غير متاح.
    """
    prof = answers.get("profile")
    if isinstance(prof, dict):
        return prof

    # محاولة توليد سريع
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
        hints = " | ".join([*z_markers, *signals])[:1000]  # نص موجز للبرومبت

        return {
            "scores": enc.get("scores", {}),
            "axes": enc.get("axes", {}),
            "preferences": preferences,
            "hints_for_prompt": hints,
            "vr_inclination": enc.get("vr_inclination", 0),
            "confidence": enc.get("confidence", 0.0),
        }
    except Exception:
        return None

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

# كلمات/أنماط محظورة (أرقام زمن/عدّات/تكلفة/مكان مباشر) – شملت صيغ «داخلية/خارجية»
_FORBIDDEN_SENT = re.compile(
    r"(\b\d+(\.\d+)?\s*(?:min|mins|minute|minutes|second|seconds|hour|hours|دقيقة|دقائق|ثانية|ثواني|ساعة|ساعات)\b|"
    r"(?:rep|reps|set|sets|تكرار|عدة|عدات|جولة|جولات|×)|"
    r"(?:تكلفة|ميزانية|cost|budget|ريال|دولار|\$|€)|"
    r"(?:بالبيت|في\s*البيت|قرب\s*المنزل|بالمنزل|في\s*النادي|في\s*الجيم|صالة|نادي|جيم|غرفة|ساحة|ملعب|حديقة|شاطئ|"
    r"طبيعة|خارجي(?:ة)?|داخل(?:ي|ية)?|outdoor|indoor|park|beach|gym|studio))",
    re.IGNORECASE
)

def _mask_names(t: str) -> str: return _name_re.sub("—", t or "")
def _violates(t: str) -> bool:   return bool(_name_re.search(t or ""))

def _split_sentences(text: str) -> List[str]:
    if not text: return []
    return [s.strip() for s in re.split(r"(?<=[\.\!\?؟])\s+|[\n،]+", text) if s.strip()]

def _scrub_forbidden(text: str) -> str:
    """يحذف أي جملة تتضمن مكان/زمن/تكلفة/عدّات/جولات بالكامل."""
    kept = [s for s in _split_sentences(text) if not _FORBIDDEN_SENT.search(s)]
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
        if isinstance(a, list): a = ", ".join(map(str, a))
        out.append(f"- {q}: {a}")
    return "\n".join(out)

def _too_generic(text: str, min_chars: int = 280) -> bool:
    t = (text or "").strip()
    return len(t) < min_chars or any(p in t for p in _AVOID_GENERIC)

def _has_sensory(text: str, min_hits: int = 3) -> bool:
    return sum(1 for w in _SENSORY if w in (text or "")) >= min_hits

def _is_meaningful(rec: Dict[str, Any]) -> bool:
    blob = " ".join([
        rec.get("scene",""), rec.get("inner_sensation",""),
        rec.get("why_you",""), rec.get("first_week",""),
        rec.get("progress_markers","")
    ]).strip()
    return len(blob) >= 80

# ========= Alignment with Z-axes (هام لتحسين الجودة) =========
_AR_TOK = {
    "calm": ["هدوء","تنفّس","بطيء","استرخاء","صفاء","يركّز","سكون"],
    "adren": ["اندفاع","سريع","انفجار","إثارة","مجازفة","اشتباك","قوة لحظية"],
    "solo": ["لوحدك","فردي","مع نفسك","ذاتية"],
    "group": ["مع ناس","جماعة","شريك","فريق","تفاعل"],
    "tech": ["تفاصيل","إتقان","تقنية","صقل","ضبط","تكرار واعٍ"],
    "intu": ["إحساسك","حدس","تلقائي","على المزاج","بديهة"]
}
_EN_TOK = {
    "calm": ["calm","slow","breath","quiet","settle","soft","mindful"],
    "adren": ["fast","burst","risk","edge","explosive","adrenaline"],
    "solo": ["solo","alone","by yourself","individual"],
    "group": ["with people","partner","team","group","social"],
    "tech": ["detail","technique","repeat to perfect","precise","drill"],
    "intu": ["by feel","intuitive","impulsive","flow with it","go with it"]
}

def _axes_expectations(axes: Dict[str, float], lang: str) -> Dict[str, List[str]]:
    tok = _AR_TOK if lang == "العربية" else _EN_TOK
    out: Dict[str, List[str]] = {}
    if not isinstance(axes, dict): return out
    # calm_adrenaline ∈ [-1..+1]
    ca = axes.get("calm_adrenaline")
    if isinstance(ca, (int, float)):
        out["calm_adrenaline"] = tok["adren"] if ca >= 0.5 else tok["calm"] if ca <= -0.5 else []
    # solo_group
    sg = axes.get("solo_group")
    if isinstance(sg, (int, float)):
        out["solo_group"] = tok["group"] if sg >= 0.5 else tok["solo"] if sg <= -0.5 else []
    # tech_intuition
    ti = axes.get("tech_intuition")
    if isinstance(ti, (int, float)):
        out["tech_intuition"] = tok["intu"] if ti >= 0.5 else tok["tech"] if ti <= -0.5 else []
    return out

def _mismatch_with_axes(rec: Dict[str, Any], axes: Dict[str, float], lang: str) -> bool:
    exp = _axes_expectations(axes or {}, lang)
    if not exp: return False
    blob = " ".join(str(rec.get(k,"")) for k in ("scene","inner_sensation","why_you","first_week"))
    blob_l = blob.lower()
    # إذا في توقع كلمات ولم نجد أي كلمة مقابلة → تعارض
    for k, words in exp.items():
        if words and not any(w.lower() in blob_l for w in words):
            return True
    return False

def _sanitize_record(r: Dict[str, Any]) -> Dict[str, Any]:
    """ينظّف حقول التوصية من المحظورات ويشيل practical_fit إن وُجد."""
    r = dict(r or {})
    r.pop("practical_fit", None)  # حذف الحقل بالكامل
    for k in ("scene","inner_sensation","why_you","first_week","progress_markers","vr_idea"):
        if isinstance(r.get(k), str):
            r[k] = _scrub_forbidden(_mask_names(r[k].strip()))
    try:
        d = int(r.get("difficulty", 3))
        r["difficulty"] = max(1, min(5, d))
    except Exception:
        r["difficulty"] = 3
    return r

def _fallback_identity(i: int, lang: str) -> Dict[str, Any]:
    """فولباك بلا أرقام ولا مكان/زمن/تكلفة — بصياغة حسّية إنسانية."""
    if lang == "العربية":
        presets = [
            {
                "scene":"إحساس انسيابي بإيقاع لطيف يفتح النفس تدريجيًا.",
                "inner_sensation":"دفء هادئ ووضوح بسيط في التفكير.",
                "why_you":"تحب التقدّم السلس وتكره الرتابة. تبغى سيطرة داخلية بدون تعقيد.",
                "first_week":"ابدأ بحركات تفتح النفس بلطف، ثم وسّع المدى حسب الإحساس.",
                "progress_markers":"تنفّس أهدأ، صفاء بعد الجلسة، رغبة طبيعية للاستمرار.",
                "difficulty":2,
                "vr_idea":"نسخة افتراضية خفيفة تُبرز الإيقاع والتتبّع."
            },
            {
                "scene":"حركة متناغمة تُشغّل الجذع والذراعين بإحساس ثابت.",
                "inner_sensation":"حرارة خفيفة مع تماسك في الوسط.",
                "why_you":"تبغى تقدّم واضح وقابل للملاحظة بدون فلسفة زايدة.",
                "first_week":"شغّل الجذع بحركات بسيطة، واختم بمرونة هادئة.",
                "progress_markers":"ثبات أقوى، نوم أعمق، طاقة أهدأ خلال اليوم.",
                "difficulty":3,
                "vr_idea":"محاكاة توازن بسيطة لتعزيز التمركز."
            },
            {
                "scene":"إيقاع هادئ يسمح للجهاز العصبي يهدأ تدريجيًا.",
                "inner_sensation":"تفكّك لطيف للتوتر وإحساس رايق.",
                "why_you":"تحتاج إعادة ضبط ترفع تقبّل الجهد خطوة بخطوة.",
                "first_week":"تابع النفس، وحرّك ببطء، وأضف تمديدات مرنة على مزاجك.",
                "progress_markers":"توتر أقل، تركيز أوضح، توازن أفضل.",
                "difficulty":1,
                "vr_idea":"طبيعة افتراضية للاسترخاء الذهني."
            }
        ]
    else:
        presets = [
            {
                "scene":"A smooth, easy rhythm that opens the breath.",
                "inner_sensation":"Warm calm and simple mental clarity.",
                "why_you":"You like steady progress and dislike boredom.",
                "first_week":"Open the breath gently, then widen range by feel.",
                "progress_markers":"Calmer breath, post-session clarity, natural urge to continue.",
                "difficulty":2,
                "vr_idea":"Light VR emphasizing rhythm and tracking."
            },
            {
                "scene":"Harmonious flow engaging trunk and arms with steadiness.",
                "inner_sensation":"Gentle heat and centered feel.",
                "why_you":"You want noticeable progress without overthinking.",
                "first_week":"Activate the core with simple moves; close with soft mobility.",
                "progress_markers":"Stronger stability, deeper sleep, steadier energy.",
                "difficulty":3,
                "vr_idea":"Simple balance simulation to reinforce centering."
            },
            {
                "scene":"Quiet tempo that lets the nervous system settle.",
                "inner_sensation":"Tension eases; mind feels clear.",
                "why_you":"You need a gentle reset to raise effort tolerance.",
                "first_week":"Track your breath and move slowly; add elastic stretches by feel.",
                "progress_markers":"Less neck/jaw tension, clearer focus, better balance.",
                "difficulty":1,
                "vr_idea":"Immersive nature-relax VR."
            }
        ]
    return presets[i % 3]

def _json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                 personality: Any, lang: str) -> List[Dict[str, str]]:
    bullets = _answers_to_bullets(answers)
    persona = personality if isinstance(personality, str) else json.dumps(personality, ensure_ascii=False)

    # (جديد) حوافز البروفايل المُشفَّر إن وُجد
    profile = analysis.get("encoded_profile")
    profile_hints = ""
    if isinstance(profile, dict):
        profile_hints = profile.get("hints_for_prompt", "") or ", ".join(profile.get("preferences", {}).values())

    if lang == "العربية":
        sys = (
            "أنت مدرّب SportSync AI بنبرة إنسانية لطيفة (صديق محترف). "
            "لا تذكر المكان/الزمن/التكلفة/العدّات/الجولات أو أي أرقام دقائق. "
            "استخدم لغة حسّية واضحة وقوائم قصيرة. أعِد JSON فقط."
        )
        usr = (
            "حوّل بيانات المستخدم إلى ثلاث توصيات حركة بلا أسماء رياضات.\n"
            "أعِد JSON فقط بالمفاتيح:\n"
            "{\"recommendations\":[{\"scene\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\","
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            "قواعد الأسلوب:\n"
            "- لهجة صديق مهني وقصيرة.\n"
            "- 'why_you' سبب واضح وبشري.\n"
            "- 'first_week' خطوات نوعية بلا أرقام/عدّات/دقائق.\n"
            "- 'progress_markers' مؤشرات إحساس/سلوك دون أزمنة.\n\n"
            f"— شخصية المدرب:\n{persona}\n\n"
            "— تحليل المستخدم:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— إجابات موجزة:\n" + bullets + "\n\n"
            + ("— إشارات بروفايل:\n" + profile_hints + "\n\n" if profile_hints else "")
            + "أعِد JSON فقط."
        )
    else:
        sys = (
            "You are a warm, human SportSync coach. "
            "Do NOT mention location/time/cost/reps/sets or minute counts. "
            "Use sensory, concise bullets. Return JSON only."
        )
        usr = (
            "Create THREE nameless movement-identity suggestions.\n"
            "Return JSON ONLY with:\n"
            "{\"recommendations\":[{\"scene\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\","
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            "Style rules: human tone; 'first_week' qualitative (no numbers); no place/time/cost.\n\n"
            f"— Coach persona:\n{persona}\n\n"
            "— User analysis:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— Bulleted answers:\n" + bullets + "\n\n"
            + ("— Profile hints:\n" + profile_hints + "\n\n" if profile_hints else "")
            + "JSON only."
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

def _to_bullets(text: str, max_items: int = 5) -> List[str]:
    if not text: return []
    raw = re.split(r"[;\n\.،]+", text)
    items = [i.strip(" -•\t ") for i in raw if i.strip()]
    return items[:max_items]

def _one_liner(*parts: str, max_len: int = 120) -> str:
    s = " — ".join([p.strip() for p in parts if p and p.strip()])
    return s[:max_len]

# ======== (جديد) اسم الهوية + ملاحظات إنسانية ========

def _concept_label(rec: Dict[str, Any], axes: Dict[str, float], lang: str) -> str:
    """اسم وصفي قصير للهوية مبني على محاور Z ووجود VR (بدون أسماء رياضات)."""
    ad = float((axes or {}).get("calm_adrenaline", 0.0) or 0.0)
    ti = float((axes or {}).get("tech_intuition", 0.0) or 0.0)
    has_vr = bool((rec or {}).get("vr_idea"))

    if lang == "العربية":
        base = "تكتيكي" if ad >= 0.5 else "انسيابي" if ad <= -0.5 else "متوازن"
        layer = "حدسي" if ti >= 0.5 else "دقيق" if ti <= -0.5 else "مرن"
        extra = "غامر" if has_vr else "مركّز"
        name = f"{base} {extra}"
        if layer in ("حدسي","دقيق"):
            name = f"{name} {layer}"
        return name
    else:
        base = "Tactical" if ad >= 0.5 else "Fluid" if ad <= -0.5 else "Balanced"
        layer = "Intuitive" if ti >= 0.5 else "Precise" if ti <= -0.5 else "Adaptive"
        extra = "Immersive" if has_vr else "Focused"
        name = f"{base} {extra}"
        if layer in ("Intuitive","Precise"):
            name = f"{name} {layer}"
        return name

def _notes_block(rec: Dict[str, Any], lang: str) -> List[str]:
    """ملاحظات إنسانية قصيرة (تبقى عامة؛ بدون مكان/زمن/تكلفة)."""
    notes: List[str] = []
    vr = (rec.get("vr_idea") or "").strip()
    if lang == "العربية":
        notes.append("هذه «هوية حركة» وصفية، مو لازم تسميها رياضة.")
        if vr: notes.append(vr)
        notes.append("تبغى تفاصيل أدوات/أماكن؟ اسألني في الشات ونخصصها لك.")
    else:
        notes.append("This is a descriptive movement identity, not a sport label.")
        if vr: notes.append(vr)
        notes.append("Want gear/venue specifics? Ask in chat and we’ll tailor it.")
    return notes[:3]

def _format_card(rec: Dict[str, Any], i: int, lang: str) -> str:
    axes_for_title = rec.get("_axes_for_title") or {}
    concept = _concept_label(rec, axes_for_title, lang)

    # رؤوس
    head_ar = ["🟢 التوصية 1","🌿 التوصية 2","🔮 التوصية 3 (ابتكارية)"]
    head_en = ["🟢 Rec #1","🌿 Rec #2","🔮 Rec #3 (Creative)"]
    head = (head_ar if lang == "العربية" else head_en)[i]

    # عناصر
    scene = (rec.get("scene") or "").strip()
    inner = (rec.get("inner_sensation") or "").strip()
    why   = (rec.get("why_you") or "").strip()
    week  = _to_bullets(rec.get("first_week") or "")
    prog  = _to_bullets(rec.get("progress_markers") or "", max_items=4)
    diff  = rec.get("difficulty", 3)

    intro = _one_liner(scene, inner)
    notes = _notes_block(rec, lang)

    if lang == "العربية":
        out = [head, "", f"🎯 الهوية المثالية لك: {concept}", ""]
        if intro:
            out += ["💡 ما هي؟", f"- {intro}", ""]
        if why:
            out += ["🎮 ليه تناسبك؟"]
            for b in _to_bullets(why, 4) or [why]:
                out.append(f"- {b}")
            out.append("")
        if week:
            out += ["🔍 شكلها الواقعي:"]
            for b in week: out.append(f"- {b}")
            out.append("")
        if prog:
            out += ["📈 علامات تقدّم محسوسة:"]
            for b in prog: out.append(f"- {b}")
            out.append("")
        out.append(f"المستوى التقريبي: {diff}/5")
        if notes:
            out += ["", "👁‍🗨 ملاحظات:"]
            for n in notes: out.append(f"- {n}")
        return "\n".join(out)
    else:
        out = [head, "", f"🎯 Ideal identity: {concept}", ""]
        if intro:
            out += ["💡 What is it?", f"- {intro}", ""]
        if why:
            out += ["🎮 Why it suits you"]
            for b in _to_bullets(why, 4) or [why]:
                out.append(f"- {b}")
            out.append("")
        if week:
            out += ["🔍 Real-world feel:"]
            for b in week: out.append(f"- {b}")
            out.append("")
        if prog:
            out += ["📈 Progress cues:"]
            for b in prog: out.append(f"- {b}")
            out.append("")
        out.append(f"Approx level: {diff}/5")
        if notes:
            out += ["", "👁‍🗨 Notes:"]
            for n in notes: out.append(f"- {n}")
        return "\n".join(out)

def _sanitize_fill(recs: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        # mask + scrub + drop practical_fit
        r = _sanitize_record(r)

        # quality gate
        blob = " ".join([
            r.get("scene",""), r.get("inner_sensation",""),
            r.get("why_you",""), r.get("first_week",""),
            r.get("progress_markers","")
        ])
        if _too_generic(blob) or not _has_sensory(blob) or not _is_meaningful(r):
            r = _fallback_identity(i, lang)
        out.append(r)
    return out

# ========= PUBLIC API =========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية", user_id: str = "N/A") -> List[str]:
    if OpenAI_CLIENT is None:
        return ["❌ OPENAI_API_KEY غير مضبوط في خدمة الـ Quiz.", "—", "—"]

    # تحليل المستخدم + طبقة Z
    analysis = analyze_user_from_answers(answers)
    silent = analyze_silent_drivers(answers, lang=lang) or []
    analysis["silent_drivers"] = silent

    # (جديد) التقاط بروفايل الترميز إن وُجد (أو توليده)
    profile = _extract_profile(answers, lang)
    if profile:
        analysis["encoded_profile"] = profile
        if "axes" in profile:
            analysis["z_axes"] = profile["axes"]
        if "scores" in profile:
            analysis["z_scores"] = profile["scores"]

    # شخصية المدرب من الكاش
    persona = get_cached_personality(analysis, lang=lang)
    if not persona:
        persona = {"name":"SportSync Coach","tone":"حازم-هادئ","style":"حسّي واقعي إنساني","philosophy":"هوية حركة بلا أسماء"}
        try:
            save_cached_personality(analysis, persona, lang=lang)
        except Exception:
            pass

    # === أول محاولة
    msgs = _json_prompt(analysis, answers, persona, lang)
    try:
        resp = OpenAI_CLIENT.chat.completions.create(
            model=CHAT_MODEL, messages=msgs, temperature=0.9, max_tokens=1200
        )
        raw1 = (resp.choices[0].message.content or "").strip()
        print(f"[AI] model={CHAT_MODEL} len={len(raw1)} raw[:120]={raw1[:120]!r}")
    except Exception as e:
        return [f"❌ خطأ اتصال النموذج: {e}", "—", "—"]

    # Sanitization pass-1
    if _violates(raw1): raw1 = _mask_names(raw1)
    parsed = _parse_json(raw1) or []
    cleaned = _sanitize_fill(parsed, lang)

    # ===== بوابة محاذاة Z-axes + إصلاح بنبرة إنسانية =====
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    mismatch_axes = any(_mismatch_with_axes(rec, axes, lang) for rec in cleaned)

    # فحص الجودة ومحاولة إصلاح ثانية
    need_repair_generic = any(_too_generic(" ".join([c.get("scene",""), c.get("why_you","")])) for c in cleaned)
    need_repair = need_repair_generic or mismatch_axes

    if need_repair:
        # نبني تلميحات محاذاة للموديل
        exp = _axes_expectations(axes or {}, lang)
        align_hint = ""
        if exp:
            if lang == "العربية":
                align_hint = (
                    "حاذِ التوصيات مع محاور Z:\n"
                    f"- هدوء/أدرينالين → استخدم مفردات: {', '.join(exp.get('calm_adrenaline', []))}\n"
                    f"- فردي/جماعي → مفردات: {', '.join(exp.get('solo_group', []))}\n"
                    f"- تقني/حدسي → مفردات: {', '.join(exp.get('tech_intuition', []))}\n"
                )
            else:
                align_hint = (
                    "Align with Z-axes:\n"
                    f"- Calm/Adrenaline words: {', '.join(exp.get('calm_adrenaline', []))}\n"
                    f"- Solo/Group words: {', '.join(exp.get('solo_group', []))}\n"
                    f"- Technical/Intuitive words: {', '.join(exp.get('tech_intuition', []))}\n"
                )

        repair_prompt = {
            "role":"user",
            "content":(
                ("أعد صياغة التوصيات بنبرة إنسانية حارة وواضحة. " if lang=="العربية"
                 else "Rewrite with a warm, human tone. ") +
                "تذكير صارم: لا مكان/زمن/تكلفة ولا أرقام/عدّات/جولات/دقائق. "
                "املأ why_you و first_week بعناصر حسّية نوعية. JSON فقط.\n\n" +
                align_hint
            )
        }
        try:
            resp2 = OpenAI_CLIENT.chat.completions.create(
                model=CHAT_MODEL,
                messages=msgs + [{"role":"assistant","content":raw1}, repair_prompt],
                temperature=0.85, max_tokens=1200
            )
            raw2 = (resp2.choices[0].message.content or "").strip()
            if _violates(raw2): raw2 = _mask_names(raw2)
            parsed2 = _parse_json(raw2) or []
            cleaned2 = _sanitize_fill(parsed2, lang)

            # اختر الأفضل بحِسّية أطول
            def score(r: Dict[str,Any]) -> int:
                txt = " ".join([
                    r.get("scene",""),
                    r.get("inner_sensation",""),
                    r.get("why_you",""),
                    r.get("first_week","")
                ])
                return len(txt)

            if sum(map(score, cleaned2)) > sum(map(score, cleaned)):
                cleaned = cleaned2
        except Exception:
            pass

    # مرّر محاور Z لتوليد العنوان ثم احذف المؤقت
    axes_for_title = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    for r in cleaned:
        r["_axes_for_title"] = axes_for_title
    cards = [_format_card(cleaned[i], i, lang) for i in range(3)]
    for r in cleaned:
        r.pop("_axes_for_title", None)

    # لوق مع أعلام الجودة
    quality_flags = {
        "generic": any(_too_generic(" ".join([c.get("scene",""), c.get("why_you","")])) for c in cleaned),
        "low_sensory": any(not _has_sensory(" ".join([c.get("scene",""), c.get("inner_sensation","")])) for c in cleaned),
        "mismatch_axes": mismatch_axes
    }

    try:
        log_user_insight(
            user_id=user_id,
            content={
                "language": lang,
                "answers": {k: v for k, v in answers.items() if k != "profile"},
                "analysis": analysis,
                "silent_drivers": silent,
                "encoded_profile": profile,
                "recommendations": cleaned,
                "quality_flags": quality_flags
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    return cards
