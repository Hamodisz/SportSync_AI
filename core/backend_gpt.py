# -- coding: utf-8 --
"""
core/backend_gpt.py
-------------------
توليد توصيات رياضية ذكية (3 توصيات) مع تحليل طبقة Z وشخصية مدرّب متكيفة.
- إخراج منسّق ومتّسق (نحاول JSON أولاً ثم فولباك تقسيم نص).
- يدعم العربية والإنجليزية تلقائيًا.
- يسجّل كل شيء في user_logger للتعلّم المستمر.
"""

from _future_ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional

# ========== OpenAI client ==========
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("الرجاء إضافة حزمة OpenAI في requirements: openai>=1.6.1,<2") from e

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # لا نرمي Exception لكي لا ينهار السيرفر؛ سنعيد رسالة ودية من الدالة لاحقاً.
    OpenAI_CLIENT = None
else:
    OpenAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")  # غيّرها إلى gpt-4o-mini للتكلفة

# ========== Project imports (مع فولباكات آمنة) ==========
try:
    from core.shared_utils import generate_main_prompt as _legacy_generate_main_prompt  # لو عندك قديم
except Exception:
    _legacy_generate_main_prompt = None

try:
    from core.shared_utils import build_dynamic_personality
except Exception:
    def build_dynamic_personality(user_analysis: Dict[str, Any], lang: str = "العربية") -> str:
        return "مدرب هادئ، عملي ومحفّز، يعطي خطوات واضحة قابلة للتنفيذ أسبوعياً."

try:
    from core.user_logger import log_user_insight
except Exception:
    def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "event") -> None:
        # فولباك: اطبع فقط
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
        # فولباك مبسّط
        return {"quick_profile": "fallback", "raw_answers": answers}

try:
    from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
        return ["انجازات قصيرة", "ميول فردية", "حساسية للملل"]


# ========== Helpers ==========
def _answers_to_bullets(answers: Dict[str, Any], lang: str) -> str:
    """
    نحول answers إلى نقاط مختصرة مفهومة للنموذج.
    توقعنا شكل answers من واجهة الأسئلة: {q_key: {"question":..., "answer":...}}
    لكن لو جاءك سكيم مختلف، نحاول نحوله لنص بشكل مرن.
    """
    try:
        items = []
        for k, v in answers.items():
            if isinstance(v, dict):
                q = v.get("question", k)
                a = v.get("answer", "")
            else:
                q = str(k)
                a = str(v)
            if isinstance(a, list):
                a_txt = ", ".join(map(str, a))
            else:
                a_txt = str(a)
            items.append(f"- {q}: {a_txt}")
        return "\n".join(items)
    except Exception:
        # فولباك: JSON خام
        return json.dumps(answers, ensure_ascii=False)

def _build_json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                       personality: str, lang: str) -> List[Dict[str, str]]:
    """
    نستخدم رسائل system+user ونطلب JSON صارم لثلاث توصيات.
    """
    bullets = _answers_to_bullets(answers, lang)
    silent = analysis.get("silent_drivers", [])

    if lang == "العربية":
        system_txt = (
            "أنت مدرب ذكاء اصطناعي محترف. استخدم أسلوباً واضحاً، محترماً، ومحفزاً. "
            "طابق نبرة الرد مع شخصية المدرب التالية: " + personality + " "
            "قيّم دوافع المستخدم (طبقة Z) وعدّل الخطة لتكون قابلة للتنفيذ الآن."
        )
        user_txt = (
            "حوّل بيانات المستخدم التالية إلى ثلاث توصيات رياضية مخصّصة. "
            "أعد النتيجة بصيغة JSON فقط، مفاتيحها: recommendations=[{title, plan, why, difficulty (1-5), gear, vr_idea?}].\n"
            "تجنّب أي نص خارج JSON.\n\n"
            "— تحليل المستخدم:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— إجابات المستخدم (مختصرة):\n" + bullets + "\n\n"
            "— مراعاة طبقة Z:\n" + ", ".join(silent) + "\n\n"
            "الاشتراطات:\n"
            "- ثلاث توصيات فقط.\n"
            "- لكل توصية: عنوان موجز (title)، خطة عملية أسبوعية (plan) بخطوات مرقمة، لماذا هذا مناسب (why)، مستوى صعوبة (difficulty 1-5)، معدات إن لزم (gear)، وفكرة واقع افتراضي إن مناسبة (vr_idea).\n"
            "- الرد بصيغة JSON بدون شرح إضافي."
        )
    else:
        system_txt = (
            "You are a professional AI coach. Be clear, respectful, and motivating. "
            "Match the tone with this coach personality: " + personality + ". "
            "Leverage Layer-Z drivers to tailor actionable steps the user can start now."
        )
        user_txt = (
            "Turn the following user data into THREE tailored sport recommendations. "
            "Return JSON ONLY with the shape: {\"recommendations\":[{\"title\":\"...\",\"plan\":\"...\",\"why\":\"...\",\"difficulty\":1-5,\"gear\":\"...\",\"vr_idea\":\"...\"}]}.\n"
            "No text outside JSON.\n\n"
            "— User analysis:\n" + json.dumps(analysis, ensure_ascii=False) + "\n\n"
            "— User answers (bulleted):\n" + bullets + "\n\n"
            "— Layer-Z drivers to respect:\n" + ", ".join(silent) + "\n\n"
            "Constraints:\n"
            "- Exactly three items.\n"
            "- Each with: short title, weekly step-by-step plan, why it fits, difficulty 1–5, gear (if any), optional VR idea.\n"
            "- JSON only, no extra prose."
        )

    return [
        {"role": "system", "content": system_txt},
        {"role": "user", "content": user_txt}
    ]

def _parse_json_or_fallback(text: str, lang: str) -> List[Dict[str, Any]]:
    """
    نحاول نحصل JSON. إذا فشلنا، نستخدم Regex لاستخراج كتلة JSON.
    وإن فشلنا تماماً نرجع 3 بلوكات نصية مقسمة.
    """
    # 1) محاولة JSON مباشرة
    try:
        obj = json.loads(text)
        recs = obj.get("recommendations", [])
        if isinstance(recs, list) and recs:
            return recs[:3]
    except Exception:
        pass

    # 2) استخرج أقرب كتلة JSON
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            obj = json.loads(m.group(0))
            recs = obj.get("recommendations", [])
            if isinstance(recs, list) and recs:
                return recs[:3]
    except Exception:
        pass

    # 3) فولباك نصّي: نفصل إلى 3 مقاطع
    parts: List[str] = []
    buf: List[str] = []
    for line in text.splitlines():
        if (line.strip().lower().startswith(("1.", "2.", "3."))) and buf:
            parts.append("\n".join(buf).strip()); buf = [line]
        else:
            buf.append(line)
    if buf:
        parts.append("\n".join(buf).strip())

    parts = parts[:3] if parts else [text.strip()]

    # رجّعها بشكل هيكلي بسيط
    out = []
    for p in parts[:3]:
        out.append({
            "title": "Recommendation" if lang != "العربية" else "توصية",
            "plan": p,
            "why": "",
            "difficulty": 3,
            "gear": "",
            "vr_idea": ""
        })
    # لو أقل من 3 كمّل
    while len(out) < 3:
        out.append({
            "title": "Recommendation" if lang != "العربية" else "توصية",
            "plan": "—",
            "why": "",
            "difficulty": 3,
            "gear": "",
            "vr_idea": ""
        })
    return out[:3]

def _format_card(rec: Dict[str, Any], idx: int, lang: str) -> str:
    """
    نرجّع نصاً لطيفاً للعرض في واجهة Streamlit (كرت لكل توصية).
    """
    num = idx + 1
    if lang == "العربية":
        head = ["🟢 التوصية 1", "🌿 التوصية 2", "🔮 التوصية 3 (ابتكارية)"][idx] if idx < 3 else f"🔹 توصية {num}"
        return (
            f"{head} — {rec.get('title','')}\n\n"
            f"*الخطة:*\n{rec.get('plan','—')}\n\n"
            f"*لماذا تناسبك:* {rec.get('why','')}\n\n"
            f"*الصعوبة:* {rec.get('difficulty',3)}/5\n"
            f"*المعدات:* {rec.get('gear','')}\n"
            f"*فكرة VR:* {rec.get('vr_idea','')}\n"
        )
    else:
        head = ["🟢 Recommendation #1", "🌿 Recommendation #2", "🔮 Recommendation #3 (Creative)"][idx] if idx < 3 else f"🔹 Recommendation {num}"
        return (
            f"{head} — {rec.get('title','')}\n\n"
            f"*Plan:*\n{rec.get('plan','—')}\n\n"
            f"*Why it fits:* {rec.get('why','')}\n\n"
            f"*Difficulty:* {rec.get('difficulty',3)}/5\n"
            f"*Gear:* {rec.get('gear','')}\n"
            f"*VR idea:* {rec.get('vr_idea','')}\n"
        )

# ========== Public API ==========
def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية", user_id: str = "N/A") -> List[str]:
    """
    ترجع قائمة من 3 نصوص منسّقة (كروت) لعرضها مباشرة في الواجهة.
    لو فقد مفتاح OpenAI -> ترجع رسالة خطأ ودّية ضمن العنصر الأول.
    """
    if OpenAI_CLIENT is None:
        return ["❌ OPENAI_API_KEY غير مضبوط. لا يمكن توليد التوصيات حالياً.", "—", "—"]

    # 1) تحليل المستخدم
    user_analysis = analyze_user_from_answers(answers)

    # 2) طبقة Z
    silent_drivers = analyze_silent_drivers(answers, lang=lang) or []
    user_analysis["silent_drivers"] = silent_drivers

    # 3) شخصية المدرب (كاش)
    personality = get_cached_personality(user_analysis, lang=lang)
    if not personality:
        personality = build_dynamic_personality(user_analysis, lang=lang)
        try:
            save_cached_personality(user_analysis, personality, lang=lang)
        except Exception:
            pass

    # 4) بناء الرسائل
    messages = _build_json_prompt(user_analysis, answers, personality, lang)

    # 5) استدعاء النموذج
    try:
        completion = OpenAI_CLIENT.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=900
        )
        raw = (completion.choices[0].message.content or "").strip()
    except Exception as e:
        return [f"❌ خطأ في اتصال النموذج: {e}", "—", "—"]

    # 6) تفكيك الرد إلى 3 عناصر
    parsed = _parse_json_or_fallback(raw, lang=lang)

    # 7) تنسيق العرض للكروت
    cards = [_format_card(rec, i, lang) for i, rec in enumerate(parsed[:3])]

    # 8) تسجيل للأثر/التعلّم
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
                "parsed": parsed
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    return cards
