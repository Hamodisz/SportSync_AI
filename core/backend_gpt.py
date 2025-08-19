# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
توصيات "هوية رياضية بلا أسماء" بثلاث كروت حسّية منظمة + طبقة Z + خطة أسبوع (نوعية فقط) + فكرة VR.
- لا مكان/زمن/تكلفة ولا عدّات/جولات/دقائق في الإخراج.
- يحاول مرتين قبل السقوط للـ fallback. يدعم العربية/English.
"""

from __future__ import annotations

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

# كلمات/أنماط محظورة (أرقام زمن/عدّات/تكلفة/مكان مباشر)
_NUM_TIME_COST_PAT = re.compile(
    r"(\b\d+(\.\d+)?\b|\b\d+\s*(min|mins|minute|minutes|second|seconds|hour|hours|جولة|جولات|عدة|عدات|دقيقة|دقائق|ساعة|ساعات)\b|"
    r"تكلفة|cost|budget|ريال|دولار|$|€|مكان|near home|بالبيت|في النادي|في الجيم)",
    re.IGNORECASE
)

def _mask_names(t: str) -> str: return _name_re.sub("—", t or "")
def _violates(t: str) -> bool:   return bool(_name_re.search(t or ""))

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

def _strip_forbidden(text: str) -> str:
    """يزيل الأرقام ودقائق/جولات/تكلفة/مكان مباشر من النص."""
    if not text: return text
    return _NUM_TIME_COST_PAT.sub("", text)

def _sanitize_record(r: Dict[str, Any]) -> Dict[str, Any]:
    """ينظّف حقول التوصية من المحظورات ويشيل practical_fit إن وُجد."""
    r = dict(r or {})
    r.pop("practical_fit", None)  # حذف الحقل بالكامل

    for k in ("scene","inner_sensation","why_you","first_week","progress_markers","vr_idea"):
        if isinstance(r.get(k), str):
            r[k] = _strip_forbidden(_mask_names(r[k].strip()))
    # ضبط الصعوبة ضمن 1..5
    try:
        d = int(r.get("difficulty", 3))
        r["difficulty"] = max(1, min(5, d))
    except Exception:
        r["difficulty"] = 3
    return r

def _fallback_identity(i: int, lang: str) -> Dict[str, Any]:
    """فولباك بلا أرقام ولا مكان/زمن/تكلفة."""
    if lang == "العربية":
        presets = [
            {
                "scene":"مساحة مفتوحة بإحساس انسيابي وتغيّر بسيط في السطح.",
                "inner_sensation":"دفء تدريجي ووضوح ذهني هادئ.",
                "why_you":"تحب التقدّم السلس بلا رتابة وتبحث عن سيطرة داخلية بسيطة.",
                "first_week":"ابدأ بحركات تفتح النفس وتبني الإيقاع. زِد استكشاف الحركة وفق إحساسك.",
                "progress_markers":"تنفّس أهدأ، صفاء بعد الجلسة، رغبة طبيعية للاستمرار.",
                "difficulty":2,
                "vr_idea":"نسخة افتراضية خفيفة تُبرز الإيقاع والتتبع."
            },
            {
                "scene":"مساحة داخلية بسيطة تسمح بحركة متناغمة للجذع والذراعين.",
                "inner_sensation":"حرارة لطيفة مع إحساس بالتماسك في الوسط.",
                "why_you":"تحب تقدّم واضح وقابل للملاحظة دون تعقيد.",
                "first_week":"ركّز على حركات تُشغّل الجذع وتُشعر بالثبات. لاحظ حالتك قبل وبعد.",
                "progress_markers":"إحساس أقوى بالثبات، نوم أعمق، طاقة أهدأ خلال اليوم.",
                "difficulty":3,
                "vr_idea":"محاكاة توازن بسيطة لتعزيز التمركز."
            },
            {
                "scene":"مكان هادئ مع مجال رؤية واسع وحركة واعية بطيئة.",
                "inner_sensation":"تهدئة عصبية وإطالة مريحة للمفاصل.",
                "why_you":"تحتاج إعادة تنظيم شعوري ترفع تقبّل الجهد تدريجيًا.",
                "first_week":"حرّك ببطء مع متابعة النفس ثم أضف تمديدات مرنة حسب ما يناسب جسدك.",
                "progress_markers":"توتر أقل في الرقبة/الفك، تركيز أوضح، توازن أفضل.",
                "difficulty":1,
                "vr_idea":"جلسة طبيعة افتراضية للاسترخاء الذهني."
            }
        ]
    else:
        presets = [
            {
                "scene":"Open area with gentle flow and slight surface variation.",
                "inner_sensation":"Warm build-up with calm clarity.",
                "why_you":"You like smooth progress without boredom and value inner control.",
                "first_week":"Use easy movements that open your breath; explore flow by feel.",
                "progress_markers":"Calmer breath, post-session clarity, natural urge to continue.",
                "difficulty":2,
                "vr_idea":"Light rhythm/tracking VR variant."
            },
            {
                "scene":"Simple indoor space allowing rhythmic trunk and arm flow.",
                "inner_sensation":"Gentle heat with a centered core.",
                "why_you":"You want clear, noticeable progress without complexity.",
                "first_week":"Pick movements that engage the core and build stability. Note before/after.",
                "progress_markers":"Stronger stability, deeper sleep, steadier energy.",
                "difficulty":3,
                "vr_idea":"Simple balance VR to reinforce centering."
            },
            {
                "scene":"Quiet space with wide field of view and slow mindful motion.",
                "inner_sensation":"Neural calm and comfortable decompression.",
                "why_you":"You need a gentle reset that raises tolerance for effort over time.",
                "first_week":"Move slowly while tracking breath; add elastic stretches as feels right.",
                "progress_markers":"Less neck/jaw tension, clearer focus, better balance.",
                "difficulty":1,
                "vr_idea":"Immersive nature-relax session."
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
            "أنت مدرّب SportSync AI.\n"
            "- اكتب بلغة بسيطة جدًا وجُمل قصيرة.\n"
            "- لا تذكر عبارة 'Layer Z' لفظيًا؛ اشرح السبب ببساطة.\n"
            "- ممنوع: المكان/الزمن/التكلفة، وممنوع العدّات/الجولات/الدقائق.\n"
            "- استخدم قوائم نقطية واضحة.\n"
            "- أعِد JSON فقط."
        )
        usr = (
            "حوّل بيانات المستخدم إلى ثلاث توصيات حركة بلا أسماء رياضات.\n"
            "أعِد JSON فقط بالمفاتيح:\n"
            "{\"recommendations\":[{\"scene\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\","
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            "قواعد الأسلوب:\n"
            "- 'why_you' سبب واضح وبسيط.\n"
            "- 'first_week' خطوات نوعية (بدون أرقام/جولات/عدّات/دقائق).\n"
            "- 'progress_markers' علامات إحساس/سلوك بدون أرقام زمنية.\n\n"
            f"— شخصية المدرب:\n{persona}\n\n"
            "— تحليل المستخدم:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— إجابات موجزة:\n" + bullets + "\n\n"
            + ("— إشارات بروفايل:\n" + profile_hints + "\n\n" if profile_hints else "")
            + "أعِد JSON فقط، بدون أي نص خارجي."
        )
    else:
        sys = (
            "You are SportSync AI coach.\n"
            "- Very simple language, short sentences.\n"
            "- Do NOT mention 'Layer Z' explicitly; explain plainly.\n"
            "- FORBIDDEN: place/time/cost and reps/sets/minutes.\n"
            "- Use clear bullets.\n"
            "- Return JSON only."
        )
        usr = (
            "Create THREE movement-identity suggestions (no sport names).\n"
            "Return JSON ONLY with keys:\n"
            "{\"recommendations\":[{\"scene\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\","
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            "Style rules:\n"
            "- 'why_you' plain and specific.\n"
            "- 'first_week' qualitative steps (no numbers/reps/sets/minutes).\n"
            "- 'progress_markers' qualitative cues (no time numbers).\n\n"
            f"— Coach persona:\n{persona}\n\n"
            "— User analysis:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— Bulleted answers:\n" + bullets + "\n\n"
            + ("— Profile hints:\n" + profile_hints + "\n\n" if profile_hints else "")
            + "Return JSON only."
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

def _format_card(rec: Dict[str, Any], i: int, lang: str) -> str:
    head_ar = ["🟢 التوصية 1","🌿 التوصية 2","🔮 التوصية 3 (ابتكارية)"]
    head_en = ["🟢 Rec #1","🌿 Rec #2","🔮 Rec #3 (Creative)"]
    head = (head_ar if lang == "العربية" else head_en)[i]

    scene = (rec.get("scene") or "").strip()
    inner = (rec.get("inner_sensation") or "").strip()
    why   = (rec.get("why_you") or "").strip()
    week  = _to_bullets(rec.get("first_week") or "")
    prog  = _to_bullets(rec.get("progress_markers") or "", max_items=4)
    diff  = rec.get("difficulty", 3)
    vr    = (rec.get("vr_idea") or "").strip()

    intro = _one_liner(scene, inner)

    if lang == "العربية":
        out = [head, ""]
        if intro: out += ["*وش هي؟*", f"- {intro}", ""]
        if why:
            out += ["*ليش تناسبك؟*"]
            for b in _to_bullets(why, 3) or [why]:
                out.append(f"- {b}")
            out.append("")
        if week:
            out += ["*خطة أسبوع أول (نوعية)*"]
            for b in week: out.append(f"- {b}")
            out.append("")
        if prog:
            out += ["*علامات تقدّم*"]
            for b in prog: out.append(f"- {b}")
            out.append("")
        out.append(f"*الصعوبة:* {diff}/5")
        if vr: out.append(f"*VR (اختياري):* {vr}")
        return "\n".join(out)
    else:
        out = [head, ""]
        if intro: out += ["*What is it?*", f"- {intro}", ""]
        if why:
            out += ["*Why you*"]
            for b in _to_bullets(why, 3) or [why]:
                out.append(f"- {b}")
            out.append("")
        if week:
            out += ["*First week (qualitative)*"]
            for b in week: out.append(f"- {b}")
            out.append("")
        if prog:
            out += ["*Progress markers*"]
            for b in prog: out.append(f"- {b}")
            out.append("")
        out.append(f"*Difficulty:* {diff}/5")
        if vr: out.append(f"*VR (optional):* {vr}")
        return "\n".join(out)

def _sanitize_fill(recs: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        # mask names + remove forbidden numerics/place/time/cost + drop practical_fit
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
        persona = {"name":"SportSync Coach","tone":"حازم-هادئ","style":"حسّي واقعي","philosophy":"هوية حركة بلا أسماء"}
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

    # فحص الجودة ومحاولة إصلاح ثانية
    need_repair = any(_too_generic(" ".join([c.get("scene",""), c.get("why_you","")])) for c in cleaned)
    if need_repair:
        repair_prompt = {
            "role":"user",
            "content":(
                "إعادة صياغة التوصيات السابقة بجودة أعلى (بدون أسماء رياضات): "
                "التزم بعدم ذكر المكان/الزمن/التكلفة وعدم استخدام أرقام/عدّات/جولات/دقائق. "
                "املأ why_you و first_week بعناصر حسّية نوعية واضحة. "
                "أعد JSON فقط بنفس البنية."
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

    cards = [_format_card(cleaned[i], i, lang) for i in range(3)]

    try:
        log_user_insight(
            user_id=user_id,
            content={
                "language": lang,
                "answers": {k: v for k, v in answers.items() if k != "profile"},
                "analysis": analysis,
                "silent_drivers": silent,
                "encoded_profile": profile,
                "recommendations": cleaned
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    return cards
