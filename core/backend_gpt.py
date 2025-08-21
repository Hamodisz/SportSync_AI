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
"""

from __future__ import annotations

import os, json, re, hashlib
from typing import Any, Dict, List, Optional

# ========= OpenAI =========
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("أضف الحزمة في requirements: openai>=1.6.1,<2") from e

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OpenAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")  # بدّل إلى gpt-4o-mini لتكلفة أقل
ALLOW_SPORT_NAMES = True  # ✅ السماح بأسماء الأنماط/الرياضات عند الحاجة

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

# ========= Helpers: Arabic normalization =========
_AR_DIAC = r"[ًٌٍَُِّْـ]"
def _normalize_ar(t: str) -> str:
    """تطبيع مبسّط للنص العربي لتحسين المطابقة/المنع."""
    if not t: return ""
    t = re.sub(_AR_DIAC, "", t)           # إزالة التشكيل والتمطيط
    t = t.replace("أ","ا").replace("إ","ا").replace("آ","ا")
    t = t.replace("ؤ","و").replace("ئ","ي")
    t = t.replace("ة","ه").replace("ى","ي")
    t = re.sub(r"\s+", " ", t).strip()
    return t

# تحليل المستخدم — نحاول أكثر من توقيع دالة
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
    prof = answers.get("profile")
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

_FORBIDDEN_SENT = re.compile(
    r"(\b\d+(\.\d+)?\s*(?:min|mins|minute|minutes|second|seconds|hour|hours|دقيقة|دقائق|ثانية|ثواني|ساعة|ساعات)\b|"
    r"(?:rep|reps|set|sets|تكرار|عدة|عدات|جولة|جولات|×)|"
    r"(?:تكلفة|ميزانية|cost|budget|ريال|دولار|\$|€)|"
    r"(?:بالبيت|في\s*البيت|قرب\s*المنزل|بالمنزل|في\s*النادي|في\s*الجيم|صالة|نادي|جيم|غرفة|ساحة|ملعب|حديقة|شاطئ|"
    r"طبيعة|خارجي(?:ة)?|داخل(?:ي|ية)?|outdoor|indoor|park|beach|gym|studio))",
    re.IGNORECASE
)

def _contains_blocked_name(t: str) -> bool:
    """مطابقة مزدوجة: خام + بعد التطبيع."""
    if not t: return False
    return bool(_name_re.search(t)) or bool(_name_re.search(_normalize_ar(t)))

def _mask_names(t: str) -> str:
    if ALLOW_SPORT_NAMES:
        return t or ""
    # استبدال خام + بعد التطبيع (تقريبي)
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
    if lang == "العربية":
        presets = [
            {
                "sport_label":"Tactical Immersive Combat",
                "what_it_looks_like":"ساحة محاكاة بصرية أو VR: تتبّع، كمين، قرار خاطف، اقتراب محسوب، انسحاب آمن.",
                "inner_sensation":"اندماج ذهني مع يقظة عالية وثقة هادئة.",
                "why_you":"تكره التكرار وتفضّل صراعًا تكتيكيًا يختبر الذكاء والأعصاب.",
                "first_week":"ابدأ بجولة حسّية: تعرف على الإيقاع، جرّب مسار اقتراب/انسحاب، وثبّت تنفّسك قبل القرار.",
                "progress_markers":"قرارات أسرع، هدوء تحت الضغط، إحساس بسيطرة أعلى.",
                "win_condition":"الوصول لهدف دون انكشاف أو تعطيل 'الخصم' بقرار خاطف.",
                "core_skills":["تتبّع زاوية الرؤية","تغيير الإيقاع","قرار سريع","ثبات التوازن","تنفّس هادئ"],
                "mode":"Solo/Team",
                "variant_vr":"مبارزات تكتيكية في VR مع تتبع مجال رؤية الخصم.",
                "variant_no_vr":"حلبة حواجز إسفنجية مع مسارات ظلّ وتمويه.",
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
                "variant_no_vr":"حلبة خفيفة بعوائق وأشرطة ظل.",
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
                "variant_no_vr":"Foam-obstacle arena with shadow lanes.",
                "difficulty":3
            }
        ]
    return presets[i % len(presets)]

# ========= Diversity & defaults =========
def _canonical_label(label: str) -> str:
    if not label: return ""
    lab = re.sub(r"\s+", " ", label).strip(" -—:،")
    # لا نحاول title case بالعربية؛ نتركها كما هي
    return lab

def _fill_defaults(r: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """ملء الحقول الناقصة سريعاً دون تغيير أسلوب الموديل."""
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
        r["variant_no_vr"] = ("حلبة حواجز خفيفة مع ممرات ظل." if lang=="العربية"
                              else "Light obstacle arena with shadow lanes.")
    return r

def _enforce_diversity(recs: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    """منع تكرار نفس الهوية/الملمح عبر الكروت الثلاثة."""
    seen = set()
    for i, r in enumerate(recs):
        lab = _canonical_label(r.get("sport_label",""))
        if not lab:
            continue
        if lab in seen:
            # إن تكرر، نحافظ على الجوهر ونضيف تمايز واضح
            if lang == "العربية":
                r["sport_label"] = lab + " — نمط تخفّي فردي"
            else:
                r["sport_label"] = lab + " — Solo Infiltration"
        seen.add(_canonical_label(r.get("sport_label","")))
    return recs

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
            "حاذِ Z-axes بالكلمات التالية إن أمكن:\n" + axis_hint + "\n\n"
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
            "Align with Z-axes using words:\n" + axis_hint + "\n\n"
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
    out: List[Dict[str, Any]] = []
    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        r = _fill_defaults(_sanitize_record(r), lang)
        blob = " ".join([
            r.get("sport_label",""), r.get("what_it_looks_like",""),
            r.get("why_you",""), r.get("first_week",""),
            r.get("progress_markers",""), r.get("win_condition","")
        ])
        if _too_generic(blob, 220) or not _has_sensory(blob) or not _is_meaningful(r) \
           or not r.get("win_condition") or len(r.get("core_skills") or []) < 3:
            r = _fallback_identity(i, lang)
        out.append(r)
    return _enforce_diversity(out, lang)

# ========= PUBLIC API =========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية", user_id: str = "N/A") -> List[str]:
    if OpenAI_CLIENT is None:
        return ["❌ OPENAI_API_KEY غير مضبوط في خدمة الـ Quiz.", "—", "—"]

    # تحليل المستخدم + طبقة Z
    analysis = _call_analyze_user_from_answers(user_id, answers, lang)
    silent = []
    try:
        silent = analyze_silent_drivers(answers, lang=lang) or []
    except Exception:
        pass
    analysis["silent_drivers"] = silent

    # (جديد) بروفايل مُرمّز (إن وُجد)
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
            temperature=0.55,          # ↓ ثبات أعلى
            top_p=0.9,
            presence_penalty=0.2,      # تنويع طفيف
            frequency_penalty=0.15,
            max_tokens=1400
        )
        raw1 = (resp.choices[0].message.content or "").strip()
        print(f"[AI] model={CHAT_MODEL} len={len(raw1)} raw[:140]={raw1[:140]!r}")
    except Exception as e:
        return [f"❌ خطأ اتصال النموذج: {e}", "—", "—"]

    # Sanitization pass-1
    if not ALLOW_SPORT_NAMES and _contains_blocked_name(raw1):
        raw1 = _mask_names(raw1)
    parsed = _parse_json(raw1) or []
    cleaned = _sanitize_fill(parsed, lang)

    # ===== محاذاة Z-axes + إصلاح ثانٍ =====
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    mismatch_axes = any(_mismatch_with_axes(rec, axes, lang) for rec in cleaned)
    need_repair_generic = any(_too_generic(" ".join([c.get("what_it_looks_like",""), c.get("why_you","")]), 220) for c in cleaned)
    missing_fields = any((not c.get("win_condition") or len(c.get("core_skills") or []) < 3) for c in cleaned)
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
                temperature=0.6,
                top_p=0.9,
                presence_penalty=0.2,
                frequency_penalty=0.15,
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

    # بناء الكروت
    cards = [_format_card(cleaned[i], i, lang) for i in range(3)]

    # لوق مع أعلام الجودة
    quality_flags = {
        "generic": any(_too_generic(" ".join([c.get("what_it_looks_like",""), c.get("why_you","")]), 220) for c in cleaned),
        "low_sensory": any(not _has_sensory(" ".join([c.get("what_it_looks_like",""), c.get("inner_sensation","")])) for c in cleaned),
        "mismatch_axes": any(_mismatch_with_axes(c, axes, lang) for c in cleaned),
        "missing_fields": any((not c.get("win_condition") or len(c.get("core_skills") or []) < 3) for c in cleaned)
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
                "quality_flags": quality_flags,
                "seed": seed
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    return cards
