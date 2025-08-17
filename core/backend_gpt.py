# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
توصيات "هوية رياضية بلا أسماء":
- 3 توصيات بوصف حسّي + تبرير Layer Z + خطة أسبوع أول ومؤشرات تقدم.
- مخرجات منظّمة (JSON أولاً ثم فولباك).
- فلتر لمنع/تمويه أسماء الرياضات + تعبئة fallback عند النقص.
- يدعم العربية/الإنجليزية ويسجّل في user_logger.
"""

from _future_ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional

# ========== OpenAI client ==========
try:
    import openai
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("الرجاء إضافة حزمة OpenAI في requirements: openai>=1.6.1,<2") from e

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    OpenAI_CLIENT = None
else:
    OpenAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")  # غيّرها إلى gpt-4o-mini للتكلفة

# ========== Project imports (مع فولباكات آمنة) ==========
try:
    from core.shared_utils import build_main_prompt  # للديناميكي إن احتجته لاحقًا
except Exception:
    build_main_prompt = None

try:
    from core.shared_utils import generate_main_prompt  # برومبت الثلاث توصيات (مشدّد بلا أسماء)
except Exception:
    generate_main_prompt = None

try:
    from core.user_logger import log_user_insight
except Exception:
    def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "event") -> None:
        print(f"[LOG:{event_type}] {user_id}: keys={list(content.keys())}")

try:
    from core.memory_cache import get_cached_personality, save_cached_personality
except Exception:
    _PERS_CACHE: Dict[str, str] = {}
    def get_cached_personality(user_analysis: Dict[str, Any], lang: str = "العربية") -> Optional[str]:
        key = f"{lang}:{hash(json.dumps(user_analysis, ensure_ascii=False, sort_keys=True))}"
        return _PERS_CACHE.get(key)
    def save_cached_personality(user_analysis: Dict[str, Any], personality: str, lang: str = "العربية") -> None:
        key = f"{lang}:{hash(json.dumps(user_analysis, ensure_ascii=False, sort_keys=True))}"
        _PERS_CACHE[key] = personality

try:
    from core.user_analysis import analyze_user_from_answers
except Exception:
    def analyze_user_from_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
        return {"quick_profile": "fallback", "raw_answers": answers}

try:
    from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
        return ["انجازات قصيرة", "ميول فردية", "حساسية للملل"]


# ========== Block/Guard helpers ==========
# Blocklist لأسماء الرياضات (عربي/إنجليزي) – وسّعها لاحقاً عند الحاجة
_BLOCKLIST = r"(جري|ركض|سباحة|كرة|قدم|سلة|طائرة|تنس|ملاكمة|كاراتيه|كونغ فو|يوجا|يوغا|بيلاتس|رفع|أثقال|تزلج|دراج|دراجة|ركوب|خيول|باركور|جودو|سكواش|بلياردو|جولف|كرة طائرة|كرة اليد|هوكي|سباق|ماراثون|مصارعة|MMA|Boxing|Karate|Judo|Taekwondo|Soccer|Football|Basketball|Tennis|Swim|Swimming|Running|Run|Cycle|Cycling|Bike|Biking|Yoga|Pilates|Rowing|Row|Skate|Skating|Ski|Skiing|Climb|Climbing|Surf|Surfing|Golf|Volleyball|Handball|Hockey|Parkour|Wrestling)"
_name_re = re.compile(_BLOCKLIST, re.IGNORECASE)

_GENERIC_AVOID = [
    "أي نشاط بدني مفيد","اختر ما يناسبك","ابدأ بأي شيء","جرّب أكثر من خيار",
    "لا يهم النوع","تحرك فقط","نشاط عام","رياضة عامة","أنت تعرف ما يناسبك"
]

_SENSORY_HINTS = [
    "تنفّس","إيقاع","توتّر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","امتداد","حرق لطيف","صفاء","تماسك"
]

def _violates_no_name_policy(text: str) -> bool:
    return bool(_name_re.search(text or ""))

def _mask_names(text: str) -> str:
    return _name_re.sub("—", text or "")

def _has_enough_sensory(text: str, min_hits: int = 4) -> bool:
    hits = sum(1 for w in _SENSORY_HINTS if w in (text or ""))
    return hits >= min_hits

def _too_generic(text: str, min_chars: int = 380) -> bool:
    t = (text or "").strip()
    return len(t) < min_chars or any(p in t for p in _GENERIC_AVOID)

def _is_meaningful(rec: Dict[str, Any]) -> bool:
    # لازم على الأقل مشهد + لماذا أنت أو خطة أسبوع
    text = " ".join([
        (rec.get("scene") or ""),
        (rec.get("why_you") or ""),
        (rec.get("first_week") or "")
    ]).strip()
    return len(text) >= 40

def _fallback_identity(idx: int, lang: str = "العربية") -> Dict[str, Any]:
    if lang == "العربية":
        presets = [
            {
                "scene": "مسار خارجي قابل للتغيّر، سطح مرن وإيقاع متوسط مع تنفّس يفتح الصدر.",
                "inner_sensation": "تدفّق دافئ في الأطراف مع صفاء تدريجي للذهن.",
                "why_you": "تميل لإيقاع متكرر يذيب وعيك ويمنحك حرية داخلية (Layer Z).",
                "practical_fit": "20–30 دقيقة قرب المنزل، تكلفة صفر، أمان عالٍ.",
                "first_week": "٣ جلسات قصيرة، إحماء ٥ دقائق، تتبّع النفس، تدوين إحساس ما بعد.",
                "progress_markers": "انتظام النفس، رغبة لزيادة المدة، صفاء ذهني أطول.",
                "difficulty": 2,
                "vr_idea": ""
            },
            {
                "scene": "مساحة داخلية بسيطة، مقاومة للجسم بحركة متناغمة لليدين والجذع.",
                "inner_sensation": "حرارة لطيفة وتمركز في الوسط مع إحساس بالثبات.",
                "why_you": "تبحث عن إنجاز سريع وواضح بدون تعقيد (Layer Z).",
                "practical_fit": "15–20 دقيقة في المنزل، أدوات بسيطة إن لزم.",
                "first_week": "٣ جلسات، ٦ حركات أساسية × جولتين، تسجيل شدة الجهد.",
                "progress_markers": "تحكّم أفضل بالجذع، نوم أعمق، طاقة يومية أعلى.",
                "difficulty": 3,
                "vr_idea": ""
            },
            {
                "scene": "أرضية ثابتة ومجال رؤية واسع، حركة بطيئة واعية مع تمدّد متناغم.",
                "inner_sensation": "هدوء عصبيّ وإطالة للمفاصل الدقيقة.",
                "why_you": "تحتاج إعادة ضبط عصبي-عاطفي يوازن اندفاع الذهن (Layer Z).",
                "practical_fit": "10–15 دقيقة بعد الغروب، مساحة صغيرة.",
                "first_week": "حركة واعية + ٣ دورات تنفّس، تدوين إحساس قبل/بعد.",
                "progress_markers": "انخفاض توتر الرقبة/الفك، وضوح ذهني، تقبّل أعلى للجهد الهوائي.",
                "difficulty": 1,
                "vr_idea": ""
            }
        ]
    else:
        presets = [
            {
                "scene": "Outdoor path with forgiving surface; medium rhythm; open-chest breathing.",
                "inner_sensation": "Warm flow in limbs; gently clearing mind.",
                "why_you": "You sync with repetitive rhythms that dissolve awareness (Layer Z).",
                "practical_fit": "20–30 min near home; zero cost; high safety.",
                "first_week": "3 short sessions; 5-min warm-up; breath tracking; post-note.",
                "progress_markers": "Steadier breath; urge to go longer; mental clarity.",
                "difficulty": 2,
                "vr_idea": ""
            },
            {
                "scene": "Simple indoor space; body-weight resistance with rhythmic arm-torso flow.",
                "inner_sensation": "Gentle heat and centered stability.",
                "why_you": "You want quick, tangible progress without complexity (Layer Z).",
                "practical_fit": "15–20 min at home; minimal tools if any.",
                "first_week": "3 sessions; 6 basics × 2 rounds; record RPE.",
                "progress_markers": "Core control improves; deeper sleep; higher daily energy.",
                "difficulty": 3,
                "vr_idea": ""
            },
            {
                "scene": "Stable floor and wide field of view; slow aware movement with elastic stretches.",
                "inner_sensation": "Deep nervous calm and joint decompression.",
                "why_you": "You need a neuro-emotional reset to balance mental drive (Layer Z).",
                "practical_fit": "10–15 min at dusk; tiny square of space.",
                "first_week": "Mindful mobility + 3 breath cycles; log before/after.",
                "progress_markers": "Less neck/jaw tension; clearer thinking; better cardio tolerance.",
                "difficulty": 1,
                "vr_idea": ""
            }
        ]
    return presets[idx % 3]

def _answers_to_bullets(answers: Dict[str, Any], lang: str) -> str:
    try:
        items = []
        for k, v in (answers or {}).items():
            if isinstance(v, dict):
                q = v.get("question", k)
                a = v.get("answer", "")
            else:
                q = str(k); a = str(v)
            if isinstance(a, list):
                a_txt = ", ".join(map(str, a))
            else:
                a_txt = str(a)
            items.append(f"- {q}: {a_txt}")
        return "\n".join(items)
    except Exception:
        return json.dumps(answers, ensure_ascii=False)

def _build_json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                       personality: str, lang: str) -> List[Dict[str, str]]:
    """
    برومبت “هوية بلا أسماء” + JSON منظّم.
    Keys لكل توصية:
      scene, inner_sensation, why_you, practical_fit, first_week, progress_markers, difficulty(1-5), vr_idea?
    """
    bullets = _answers_to_bullets(answers, lang)
    silent = analysis.get("silent_drivers", [])
    personality_str = personality if isinstance(personality, str) else json.dumps(personality, ensure_ascii=False)

    if lang == "العربية":
        system_txt = (
            "أنت مدرّب ذكاء اصطناعي محترف من SportSync AI. امنع ذكر أسماء الرياضات والأدوات الشهيرة نهائيًا. "
            "استخدم لغة حسّية غنية، واربط كل توصية بدوافع المستخدم (طبقة Z) لتكون قابلة للتنفيذ."
        )
        user_txt = (
            "حوّل بيانات المستخدم إلى ثلاث توصيات هوية حركة بدون ذكر أسماء رياضات مطلقًا.\n"
            "أعد JSON فقط بالشكل:\n"
            "{\"recommendations\":[{\"scene\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\",\"practical_fit\":\"...\",\"first_week\":\"...\",\"progress_markers\":\"...\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            "إذا ظهر اسم رياضة فاستبدله فورًا بشرطة طويلة \"—\" مع وصف حسّي بديل.\n\n"
            f"— شخصية المدرب:\n{personality_str}\n\n"
            "— تحليل المستخدم:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— إجابات مختصرة:\n" + bullets + "\n\n"
            "— طبقة Z (اربط بها فقرة لماذا أنت):\n" + ", ".join(silent) + "\n\n"
            "قيود صارمة:\n"
            "- ثلاث توصيات فقط.\n"
            "- لغة حسّية: المكان/السطح/الإيقاع/التنفّس/نوع الجهد.\n"
            "- لكل توصية: scene, inner_sensation, why_you (Layer Z), practical_fit (زمن/مكان/تكلفة/أمان), first_week (3 خطوات), progress_markers (بعد 2–4 أسابيع), difficulty، و vr_idea إن لزم.\n"
            "- JSON فقط، بدون نص خارجي."
        )
    else:
        system_txt = (
            "You are SportSync AI coach. Never name sports or brand tools. "
            "Use rich sensory language and tie each suggestion to Layer-Z; make it actionable."
        )
        user_txt = (
            "Produce THREE movement-identity suggestions without naming any sports.\n"
            "Return JSON ONLY with:\n"
            "{\"recommendations\":[{\"scene\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\",\"practical_fit\":\"...\",\"first_week\":\"...\",\"progress_markers\":\"...\",\"difficulty\":1-5,\"vr_idea\":\"...\"}]}\n"
            "If a sport name appears, replace it with \"—\" and provide a sensory substitute.\n\n"
            f"— Coach personality:\n{personality_str}\n\n"
            "— User analysis:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— Bulleted answers:\n" + bullets + "\n\n"
            "— Layer-Z drivers:\n" + ", ".join(silent) + "\n\n"
            "Constraints:\n"
            "- Exactly three suggestions.\n"
            "- Sensory language (setting/surface/rhythm/breathing/effort).\n"
            "- Keys: scene, inner_sensation, why_you (Layer-Z), practical_fit (time/place/cost/safety), first_week (3 steps), progress_markers (2–4 weeks), difficulty, optional vr_idea.\n"
            "- JSON only."
        )

    return [
        {"role": "system", "content": system_txt},
        {"role": "user", "content": user_txt}
    ]

def _parse_json_or_fallback(text: str, lang: str) -> List[Dict[str, Any]]:
    # محاولة JSON مباشرة
    def _normalize(rec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "scene": rec.get("scene") or rec.get("plan") or "",
            "inner_sensation": rec.get("inner_sensation") or "",
            "why_you": rec.get("why_you") or rec.get("why") or "",
            "practical_fit": rec.get("practical_fit") or "",
            "first_week": rec.get("first_week") or "",
            "progress_markers": rec.get("progress_markers") or "",
            "difficulty": rec.get("difficulty", 3),
            "vr_idea": rec.get("vr_idea", "")
        }

    try:
        obj = json.loads(text)
        recs = obj.get("recommendations", [])
        if isinstance(recs, list) and recs:
            return [_normalize(r) for r in recs[:3]]
    except Exception:
        pass

    # أقرب كتلة JSON
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            obj = json.loads(m.group(0))
            recs = obj.get("recommendations", [])
            if isinstance(recs, list) and recs:
                return [_normalize(r) for r in recs[:3]]
    except Exception:
        pass

    # فولباك نصي: تقسيم إلى 3 مقاطع
    parts: List[str] = []
    buf: List[str] = []
    for line in (text or "").splitlines():
        if (line.strip().lower().startswith(("1", "1.", "٢", "2", "2.", "٣", "3", "3."))) and buf:
            parts.append("\n".join(buf).strip()); buf = [line]
        else:
            buf.append(line)
    if buf: parts.append("\n".join(buf).strip())
    parts = parts[:3] if parts else [text.strip()]

    out = []
    for p in parts[:3]:
        out.append({
            "scene": p,
            "inner_sensation": "",
            "why_you": "",
            "practical_fit": "",
            "first_week": "",
            "progress_markers": "",
            "difficulty": 3,
            "vr_idea": ""
        })
    while len(out) < 3:
        out.append(_fallback_identity(len(out), lang))
    return out[:3]

def _format_card(rec: Dict[str, Any], idx: int, lang: str) -> str:
    num = idx + 1
    if lang == "العربية":
        head = ["🟢 التجربة 1", "🌿 التجربة 2", "🔮 التجربة 3 (ابتكارية)"][idx] if idx < 3 else f"🔹 تجربة {num}"
        return (
            f"{head}\n\n"
            f"المشهد: {rec.get('scene','—')}\n\n"
            f"الإحساس الداخلي: {rec.get('inner_sensation','')}\n\n"
            f"لماذا أنت (Layer Z): {rec.get('why_you','')}\n\n"
            f"الملاءمة العملية: {rec.get('practical_fit','')}\n\n"
            f"أول أسبوع: {rec.get('first_week','')}\n\n"
            f"مؤشرات التقدم: {rec.get('progress_markers','')}\n\n"
            f"الصعوبة: {rec.get('difficulty',3)}/5\n"
            f"فكرة VR: {rec.get('vr_idea','')}\n"
        )
    else:
        head = ["🟢 Experience #1", "🌿 Experience #2", "🔮 Experience #3 (Creative)"][idx] if idx < 3 else f"🔹 Experience {num}"
        return (
            f"{head}\n\n"
            f"Scene: {rec.get('scene','—')}\n\n"
            f"Inner sensation: {rec.get('inner_sensation','')}\n\n"
            f"Why you (Layer Z): {rec.get('why_you','')}\n\n"
            f"Practical fit: {rec.get('practical_fit','')}\n\n"
            f"First week: {rec.get('first_week','')}\n\n"
            f"Progress markers: {rec.get('progress_markers','')}\n\n"
            f"Difficulty: {rec.get('difficulty',3)}/5\n"
            f"VR idea: {rec.get('vr_idea','')}\n"
        )

def _sanitize_and_fill(parsed: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    """
    - يمسّك أي أسماء لو تسرّبت داخل الحقول ويستبدلها بشرطة طويلة.
    - يرفض السطحية (قصير/عام/حسّي ضعيف) ويعطي fallback ثابت.
    - يضمن 3 توصيات دائمًا.
    """
    out: List[Dict[str, Any]] = []
    for i in range(3):
        rec = parsed[i] if i < len(parsed) else {}
        # تمويه أسماء
        for k, v in list(rec.items()):
            if isinstance(v, str) and _violates_no_name_policy(v):
                rec[k] = _mask_names(v)

        # فحص السطحية/الحسية
        text_blob = " ".join([
            rec.get("scene",""), rec.get("inner_sensation",""),
            rec.get("why_you",""), rec.get("practical_fit",""),
            rec.get("first_week",""), rec.get("progress_markers","")
        ])
        if _too_generic(text_blob) or not _has_enough_sensory(text_blob) or not _is_meaningful(rec):
            rec = _fallback_identity(i, lang)

        out.append(rec)
    return out

# ========== Public API ==========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية", user_id: str = "N/A") -> List[str]:
    if OpenAI_CLIENT is None:
        return ["❌ OPENAI_API_KEY غير مضبوط. لا يمكن توليد التوصيات حالياً.", "—", "—"]

    # [1] تحليل المستخدم
    user_analysis = analyze_user_from_answers(answers)

    # [2] طبقة Z
    silent_drivers = analyze_silent_drivers(answers, lang=lang) or []
    user_analysis["silent_drivers"] = silent_drivers

    # [3] شخصية المدرب (كاش)
    personality = get_cached_personality(user_analysis, lang=lang)
    if not personality:
        # لو ما فيه شخصية بالكاش، بنبني وحدة ديناميكيًا (اعتمدت build_main_prompt لديك)
        personality = {"name": "Sports Sync Coach", "tone": "هادئ وحازم", "style": "حسّي/واقعي", "philosophy": "هوية حركة بلا أسماء"}
        try:
            save_cached_personality(user_analysis, personality, lang=lang)
        except Exception:
            pass

    # [4] بناء الرسائل (JSON بلا أسماء)
    messages = _build_json_prompt(user_analysis, answers, personality, lang)

    # [5] استدعاء النموذج
    try:
        completion = OpenAI_CLIENT.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.85,
            max_tokens=1100
        )
        raw = (completion.choices[0].message.content or "").strip()
    except Exception as e:
        return [f"❌ خطأ في اتصال النموذج: {e}", "—", "—"]

    # [6] تمويه أسماء لو ظهرت في النص الخام (احتياط)
    if _violates_no_name_policy(raw):
        raw = _mask_names(raw)

    # [7] تفكيك الرد إلى عناصر
    parsed = _parse_json_or_fallback(raw, lang=lang)

    # [8] تنظيف/تعبئة وضمان 3 توصيات
    parsed_filled = _sanitize_and_fill(parsed, lang)

    # [9] تنسيق العرض للكروت
    cards = [_format_card(rec, i, lang) for i, rec in enumerate(parsed_filled[:3])]

    # [10] تسجيل للأثر/التعلّم
    try:
        log_user_insight(
            user_id=user_id,
            content={
                "language": lang,
                "answers": answers,
                "user_analysis": user_analysis,
                "personality_used": personality,
                "silent_drivers": silent_drivers,
                "raw_response": raw,
                "parsed": parsed,
                "final_used": parsed_filled
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    return cards
