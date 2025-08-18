# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
توصيات "هوية رياضية بلا أسماء" بثلاث كروت حسّية منظمة + طبقة Z + خطة أسبوع وبديل VR.
يحاول مرتين قبل السقوط للـ fallback. يدعم العربية/English.
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

# ========= Rules & helpers =========
_BLOCKLIST = r"(جري|ركض|سباحة|كرة|قدم|سلة|طائرة|تنس|ملاكمة|كاراتيه|كونغ فو|يوجا|يوغا|بيلاتس|رفع|أثقال|تزلج|دراج|دراجة|ركوب|خيول|باركور|جودو|سكواش|بلياردو|جولف|كرة طائرة|كرة اليد|هوكي|سباق|ماراثون|مصارعة|MMA|Boxing|Karate|Judo|Taekwondo|Soccer|Football|Basketball|Tennis|Swim|Swimming|Running|Run|Cycle|Cycling|Bike|Biking|Yoga|Pilates|Rowing|Row|Skate|Skating|Ski|Skiing|Climb|Climbing|Surf|Surfing|Golf|Volleyball|Handball|Hockey|Parkour|Wrestling)"
_name_re = re.compile(_BLOCKLIST, re.IGNORECASE)

_AVOID_GENERIC = [
    "أي نشاط بدني مفيد","اختر ما يناسبك","ابدأ بأي شيء","جرّب أكثر من خيار",
    "لا يهم النوع","تحرك فقط","نشاط عام","رياضة عامة","أنت تعرف ما يناسبك"
]
_SENSORY = [
    "تنفّس","إيقاع","توتّر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","امتداد","حرق لطيف","صفاء","تماسك"
]

def _mask_names(t: str) -> str: return _name_re.sub("—", t or "")
def _violates(t: str) -> bool:   return bool(_name_re.search(t or ""))

def _answers_to_bullets(answers: Dict[str, Any]) -> str:
    out = []
    for k, v in (answers or {}).items():
        if isinstance(v, dict):
            q, a = v.get("question", k), v.get("answer", "")
        else:
            q, a = str(k), v
        if isinstance(a, list): a = ", ".join(map(str, a))
        out.append(f"- {q}: {a}")
    return "\n".join(out)

def _too_generic(text: str, min_chars: int = 320) -> bool:
    t = (text or "").strip()
    return len(t) < min_chars or any(p in t for p in _AVOID_GENERIC)

def _has_sensory(text: str, min_hits: int = 4) -> bool:
    return sum(1 for w in _SENSORY if w in (text or "")) >= min_hits

def _is_meaningful(rec: Dict[str, Any]) -> bool:
    blob = " ".join([
        rec.get("scene",""), rec.get("inner_sensation",""),
        rec.get("why_you",""), rec.get("practical_fit",""),
        rec.get("first_week",""), rec.get("progress_markers","")
    ]).strip()
    return len(blob) >= 80

def _fallback_identity(i: int, lang: str) -> Dict[str, Any]:
    presets_ar = [
        {
            "scene":"بيئة متغيّرة السطح بإيقاع متوسط وبوابات لطاقة النفس المفتوحة.",
            "inner_sensation":"تدفّق دافئ ووضوح ذهني تدريجي.",
            "why_you":"تحب تحدّي ذاتك بدون رتابة وتبحث عن إحكام داخلي (Layer Z).",
            "practical_fit":"20–30 دقيقة قرب المنزل، تكلفة صفر، أمان عالٍ.",
            "first_week":"3 جلسات؛ 5 د دفء؛ تتبّع النفس؛ تدوين إحساس ما بعد.",
            "progress_markers":"تنفّس أهدأ، رغبة للزيادة، صفاء أطول.",
            "difficulty":2,"vr_idea":"طورها بتحديات واقع افتراضي تكتيكية خفيفة."
        },
        {
            "scene":"مساحة داخلية بسيطة وحركة مقاومة متناغمة لليدين والجذع.",
            "inner_sensation":"حرارة لطيفة وتمركز بالجذع.",
            "why_you":"تحتاج إنجاز ملموس سريع بعيدًا عن التعقيد (Layer Z).",
            "practical_fit":"15–20 دقيقة بالبيت، أدوات بسيطة.",
            "first_week":"3 جلسات؛ 6 حركات × جولتين؛ سجل شدة الجهد.",
            "progress_markers":"ثبات النواة، نوم أعمق، طاقة أعلى.",
            "difficulty":3,"vr_idea":"استخدم محاكيات وزن/توازن داخل VR."
        },
        {
            "scene":"أرضية ثابتة ومجال رؤية واسع مع تمدّد واعٍ بطيء.",
            "inner_sensation":"هدوء عصبي وتخفيف شدّ المفاصل الدقيقة.",
            "why_you":"تحتاج إعادة ضبط عصبي-عاطفي ترفع تقبّل الجهد (Layer Z).",
            "practical_fit":"10–15 دقيقة عند الغروب، مساحة صغيرة.",
            "first_week":"حركة واعية + 3 دورات تنفّس؛ مذكرات قبل/بعد.",
            "progress_markers":"توتر رقبة أقل، تفكير أصفى، تحمّل أفضل.",
            "difficulty":1,"vr_idea":"جلسات إسترخاء تفاعلية داخل الطبيعة الافتراضية."
        }
    ]
    presets_en = [
        {
            "scene":"Variable outdoor surface, medium rhythm, open-chest breathing gates.",
            "inner_sensation":"Warm limb flow; clearing mind.",
            "why_you":"Craves non-repetitive self-challenge with internal mastery (Layer Z).",
            "practical_fit":"20–30 min near home; zero cost; safe.",
            "first_week":"3 sessions; 5-min warm-up; breath tracking; post-notes.",
            "progress_markers":"Calmer breath, urge to go longer, clearer focus.",
            "difficulty":2,"vr_idea":"Light tactical VR challenges as variant."
        },
        {
            "scene":"Simple indoor space; rhythmic body-weight resistance (arms + trunk).",
            "inner_sensation":"Gentle heat; centered core stability.",
            "why_you":"Wants quick, tangible progress without complexity (Layer Z).",
            "practical_fit":"15–20 min at home; minimal tools.",
            "first_week":"3 sessions; 6 basics × 2 rounds; log RPE.",
            "progress_markers":"Core control, deeper sleep, higher energy.",
            "difficulty":3,"vr_idea":"Balance/weight simulations in VR."
        },
        {
            "scene":"Stable floor, wide FoV; slow aware movement with elastic stretches.",
            "inner_sensation":"Deep nervous calm; joint decompression.",
            "why_you":"Needs neuro-emotional reset to boost cardio tolerance (Layer Z).",
            "practical_fit":"10–15 min at dusk; tiny space.",
            "first_week":"Mindful mobility + 3 breath cycles; before/after log.",
            "progress_markers":"Less neck/jaw tension; clearer thinking.",
            "difficulty":1,"vr_idea":"Immersive nature-relax VR sessions."
        }
    ]
    return (presets_ar if lang == "العربية" else presets_en)[i % 3]

def _json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                 personality: Any, lang: str) -> List[Dict[str, str]]:
    bullets = _answers_to_bullets(answers)
    silent = analysis.get("silent_drivers", [])
    persona = personality if isinstance(personality, str) else json.dumps(personality, ensure_ascii=False)

    if lang == "العربية":
        sys = (
            "أنت مدرّب SportSync AI. امنع ذكر أسماء الرياضات/الأدوات. "
            "استخدم لغة حسّية وربط Layer-Z. أخرج JSON فقط."
        )
        usr = (
            "حوّل بيانات المستخدم إلى ثلاث توصيات هوية حركة بلا أسماء رياضات.\n"
            "Return JSON ONLY:\n"
            "{\"recommendations\":[{\"scene\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\",\"practical_fit\":\"...\","
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            "لو ظهر اسم رياضة استبدله بـ \"—\" مع بديل حسّي.\n\n"
            f"— شخصية المدرب:\n{persona}\n\n"
            "— تحليل المستخدم:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— إجابات موجزة:\n" + bullets + "\n\n"
            "— محركات Z:\n" + ", ".join(silent) + "\n\n"
            "قيود: 3 توصيات بالضبط، مشهد/إحساس/لماذا أنت/ملاءمة/أسبوع أول/مؤشرات/صعوبة/فكرة VR."
        )
    else:
        sys = (
            "You are SportSync AI coach. Never name sports. Use sensory language + Layer-Z. JSON only."
        )
        usr = (
            "Create THREE movement-identity suggestions with NO sports names.\n"
            "Return JSON ONLY with keys: scene, inner_sensation, why_you, practical_fit, first_week, progress_markers, difficulty(1-5), vr_idea.\n"
            "If a sport name appears, replace with '—' and add a sensory substitute.\n\n"
            f"— Coach persona:\n{persona}\n\n"
            "— User analysis:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— Bulleted answers:\n" + bullets + "\n\n"
            "— Layer-Z drivers:\n" + ", ".join(silent)
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

def _format_card(rec: Dict[str, Any], i: int, lang: str) -> str:
    head_ar = ["🟢 التوصية رقم 1","🌿 التوصية رقم 2","🔮 التوصية رقم 3 (ابتكارية)"]
    head_en = ["🟢 Recommendation #1","🌿 Recommendation #2","🔮 Recommendation #3 (Creative)"]
    head = (head_ar if lang == "العربية" else head_en)[i]
    return (
        f"{head}\n\n"
        f"{'المشهد' if lang=='العربية' else 'Scene'}: {rec.get('scene','—')}\n\n"
        f"{'الإحساس الداخلي' if lang=='العربية' else 'Inner sensation'}: {rec.get('inner_sensation','')}\n\n"
        f"{'لماذا أنت (Layer Z)' if lang=='العربية' else 'Why you (Layer-Z)'}: {rec.get('why_you','')}\n\n"
        f"{'الملاءمة العملية' if lang=='العربية' else 'Practical fit'}: {rec.get('practical_fit','')}\n\n"
        f"{'أول أسبوع' if lang=='العربية' else 'First week'}: {rec.get('first_week','')}\n\n"
        f"{'مؤشرات التقدم' if lang=='العربية' else 'Progress markers'}: {rec.get('progress_markers','')}\n\n"
        f"{'الصعوبة' if lang=='العربية' else 'Difficulty'}: {rec.get('difficulty',3)}/5\n"
        f"VR: {rec.get('vr_idea','')}\n"
    )

def _sanitize_fill(recs: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        # mask names
        for k, v in list(r.items()):
            if isinstance(v, str) and _violates(v):
                r[k] = _mask_names(v)
        # quality gate
        blob = " ".join([
            r.get("scene",""), r.get("inner_sensation",""),
            r.get("why_you",""), r.get("practical_fit",""),
            r.get("first_week",""), r.get("progress_markers","")
        ])
        if _too_generic(blob) or not _has_sensory(blob) or not _is_meaningful(r):
            r = _fallback_identity(i, lang)
        out.append(r)
    return out

# ========= PUBLIC API =========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية", user_id: str = "N/A") -> List[str]:
    if OpenAI_CLIENT is None:
        return ["❌ OPENAI_API_KEY غير مضبوط في خدمة الـ Quiz.", "—", "—"]

    analysis = analyze_user_from_answers(answers)
    silent = analyze_silent_drivers(answers, lang=lang) or []
    analysis["silent_drivers"] = silent

    persona = get_cached_personality(analysis, lang=lang)
    if not persona:
        persona = {"name":"SportSync Coach","tone":"حازم-هادئ","style":"حسّي واقعي","philosophy":"هوية حركة بلا أسماء"}
        try: save_cached_personality(analysis, persona, lang=lang)
        except Exception: pass

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

    if _violates(raw1): raw1 = _mask_names(raw1)
    parsed = _parse_json(raw1) or []
    cleaned = _sanitize_fill(parsed, lang)

    # هل مرّ بوابة الجودة؟ (لو أي واحدة سقطت للفولباك نحاول تحسين مرة ثانية)
    need_repair = any(_too_generic(" ".join([c.get("scene",""),c.get("why_you","")])) for c in cleaned)
    if need_repair:
        repair_prompt = {
            "role":"user",
            "content":(
                "إعادة صياغة التوصيات السابقة بجودة أعلى (بدون أسماء رياضات): "
                "املأ فجوات why_you/first_week بمزيد من الدقة الحسية والربط بـ Layer-Z. "
                "أعد JSON فقط بنفس البنية السابقة."
            )
        }
        try:
            resp2 = OpenAI_CLIENT.chat.completions.create(
                model=CHAT_MODEL, messages=msgs+[{"role":"assistant","content":raw1}, repair_prompt],
                temperature=0.85, max_tokens=1200
            )
            raw2 = (resp2.choices[0].message.content or "").strip()
            if _violates(raw2): raw2 = _mask_names(raw2)
            parsed2 = _parse_json(raw2) or []
            cleaned2 = _sanitize_fill(parsed2, lang)
            # استخدم الأفضل (الأطول حسّيًا)
            def score(r: Dict[str,Any]) -> int:
                txt = " ".join([r.get("scene",""), r.get("inner_sensation",""), r.get("why_you",""), r.get("first_week","")])
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
                "language": lang, "answers": answers, "analysis": analysis,
                "silent_drivers": silent, "recommendations": cleaned
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    return cards
