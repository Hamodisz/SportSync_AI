# -- coding: utf-8 --
"""
core/dynamic_chat.py
--------------------
محادثة تفاعلية ديناميكية مع المدرب الذكي، مدموجة مع:
- تحليل المستخدم عبر طبقات التحليل (analysis/user_analysis.py)
- طبقة Z (analysis/layer_z_engine.py)
- ترميز الإجابات إلى بروفايل سريع (core/answers_encoder.py)
- شخصية مدرّب ديناميكية (core/shared_utils.py) مع كاش (core/memory_cache.py)
- تسجيل الأثر (core/user_logger.py)

ملاحظات:
- يعتمد على OPENAI_API_KEY.
- يدعم العربية والإنجليزية.
- يحافظ على سجل المحادثة مختصر لتقليل التكلفة.
"""

from __future__ import annotations

import os
import json
import logging
from typing import List, Dict, Any, Optional

# ============== إعداد اللوجينغ ==============
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | dynamic_chat | %(message)s"
)

# ============== OpenAI Client ==============
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError(
        "حزمة openai غير مثبتة. أضفها في requirements.txt: openai>=1.6.1,<2"
    ) from e

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.warning("⚠ OPENAI_API_KEY غير مضبوط. ستفشل الدالة عند أول استدعاء لنموذج الدردشة.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")  # غيّرها لـ gpt-4o-mini لتكلفة أقل إن رغبت

# ============== استيرادات من مشروعك ==============
# طبقات التحليل + طبقة Z
try:
    from analysis.user_analysis import apply_all_analysis_layers
except Exception as e:
    logging.warning(f"Fallback: apply_all_analysis_layers غير متاحة ({e}). سيتم استخدام تحليل مبسط.")
    def apply_all_analysis_layers(text: str) -> Dict[str, Any]:
        return {"quick_profile": "fallback", "raw": text}

try:
    from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception as e:
    logging.warning(f"Fallback: analyze_silent_drivers غير متاحة ({e}).")
    def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
        return ["انجازات سريعة", "تفضيل تحديات قصيرة", "ميول فردية"]

# ترميز الإجابات إلى بروفايل (scores/prefs/signals)
try:
    from core.answers_encoder import encode_answers
except Exception as e:
    logging.warning(f"Fallback: answers_encoder غير متاح ({e}). سيتم استخدام بروفايل مبسط.")
    def encode_answers(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
        return {
            "lang": lang,
            "scores": {},
            "prefs": {"time_block": "medium", "budget_hint": "med", "environment_pref": "mixed"},
            "signals": [],
            "vr_inclination": 0
        }

# بناء البرومبت والشخصية
try:
    from core.shared_utils import build_main_prompt, build_dynamic_personality
except Exception as e:
    logging.warning(f"Fallback: build_main_prompt/build_dynamic_personality غير متاحة ({e}). سيتم استخدام قوالب مبسطة.")
    def build_dynamic_personality(user_analysis: Dict[str, Any], lang: str = "العربية") -> str:
        return "مدرب هادئ، محفّز، عملي الخطوات، يوازن بين الشدة والرحمة."
    def build_main_prompt(
        analysis: Dict[str, Any],
        answers: Dict[str, Any],
        personality: str,
        previous_recommendation: List[str],
        ratings: List[int],
        lang: str = "العربية"
    ) -> str:
        if lang == "العربية":
            return (
                "أنت مدرب ذكاء اصطناعي احترافي من SportSync AI. "
                "استخدم لهجة واضحة محترمة ونبرة محفزة. "
                "طابق الأسلوب مع شخصية المدرب التالية: " + personality + " "
                "لديك تحليل المستخدم ونتائج طبقة Z وإجابات الاستبيان وتقييماته. "
                "اكتب ردودًا قصيرة وعملية تُعدّل الخطة فورًا حسب ملاحظات المستخدم، بدون لوم."
            )
        else:
            return (
                "You are a professional AI coach from SportSync AI. "
                "Use a clear, respectful, motivating tone. "
                "Match the style with this coach personality: " + personality + " "
                "You have the user's analysis, Layer-Z drivers, survey answers and ratings. "
                "Write concise, actionable guidance and adapt the plan immediately based on feedback."
            )

# التخزين المؤقت للشخصية + التسجيل
try:
    from core.memory_cache import get_cached_personality, save_cached_personality
except Exception as e:
    logging.warning(f"Fallback: memory_cache غير متاحة ({e}). سيتم استخدام ذاكرة داخلية مؤقتة.")
    _MEM_CACHE: Dict[str, str] = {}
    def get_cached_personality(cache_key: str) -> Optional[str]:
        return _MEM_CACHE.get(cache_key)
    def save_cached_personality(cache_key: str, value: str) -> None:
        _MEM_CACHE[cache_key] = value

try:
    from core.user_logger import log_user_insight
except Exception as e:
    logging.warning(f"Fallback: user_logger غير متاحة ({e}). سيتم الطباعة للكونسول بدل التسجيل.")
    def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "chat_interaction") -> None:
        logging.info(f"[LOG:{event_type}] {user_id} -> {content.keys()}")

# ============== أدوات مساعدة ==============
def _trim_chat_history(chat_history: List[Dict[str, str]], max_msgs: int = 10) -> List[Dict[str, str]]:
    """تقليص سجل المحادثة لتقليل التكلفة وزمن الاستجابة."""
    if not chat_history:
        return []
    return chat_history[-max_msgs:]

def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(obj)

def _profile_brief(profile: Dict[str, Any], lang: str) -> str:
    """ملخّص صغير للبروفايل (signals + بعض الدرجات + التفضيلات) يُغذّى كرسالة system."""
    signals = profile.get("signals", [])
    prefs = profile.get("prefs", {})
    scores = profile.get("scores", {})
    top_scores = []
    # الترتيب حسب القيمة ثم أخذ الأعلى (حتى 5)
    for k, v in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:5]:
        top_scores.append(f"{k}:{v}")
    if lang == "العربية":
        return (
            "ملخص بروفايل مرمّز:\n"
            f"- إشارات: {', '.join(signals) if signals else 'n/a'}\n"
            f"- أعلى الدرجات: {', '.join(top_scores) if top_scores else 'n/a'}\n"
            f"- تفضيلات: وقت={prefs.get('time_block','n/a')}, ميزانية={prefs.get('budget_hint','n/a')}, بيئة={prefs.get('environment_pref','n/a')}\n"
        )
    else:
        return (
            "Encoded profile brief:\n"
            f"- Signals: {', '.join(signals) if signals else 'n/a'}\n"
            f"- Top scores: {', '.join(top_scores) if top_scores else 'n/a'}\n"
            f"- Prefs: time={prefs.get('time_block','n/a')}, budget={prefs.get('budget_hint','n/a')}, env={prefs.get('environment_pref','n/a')}\n"
        )

# ============== الدالة الرئيسية ==============
def start_dynamic_chat(
    answers: Dict[str, Any],
    previous_recommendation: List[str],
    ratings: List[int],
    user_id: str,
    lang: str = "العربية",
    chat_history: Optional[List[Dict[str, str]]] = None,
    user_message: str = ""
) -> str:
    """
    محادثة ديناميكية مع المدرب الذكي (طبقة Z + شخصية ديناميكية + بروفايل مرمّز + سجل محادثة).
    ترجع نص ردّ المدرب.
    """
    try:
        if client is None:
            return "❌ لا يمكن تشغيل المحادثة: مفتاح OPENAI_API_KEY غير مضبوط."

        # 1) تحليل المستخدم الكامل
        user_analysis = apply_all_analysis_layers(_safe_json(answers))

        # 2) طبقة Z
        try:
            z = analyze_silent_drivers(answers, lang=lang) or []
        except Exception as e:
            logging.warning(f"Layer Z failed: {e}")
            z = []
        user_analysis["silent_drivers"] = z

        # 3) ترميز الإجابات إلى بروفايل سريع (scores/prefs/signals)
        try:
            encoded_profile = encode_answers(answers, lang)
        except Exception as e:
            logging.warning(f"answers_encoder failed: {e}")
            encoded_profile = {"lang": lang, "scores": {}, "prefs": {}, "signals": [], "vr_inclination": 0}
        user_analysis["encoded_profile"] = encoded_profile

        # 4) شخصية المدرب مع كاش (مفتاح الكاش يتضمن البروفايل لضمان ثبات الأسلوب)
        cache_key = f"{lang}:{hash(_safe_json({'ua': user_analysis.get('quick_profile',''), 'scores': encoded_profile.get('scores', {}), 'prefs': encoded_profile.get('prefs', {})}))}"
        personality = get_cached_personality(cache_key)
        if not personality:
            personality = build_dynamic_personality(user_analysis, lang)
            save_cached_personality(cache_key, personality)

        # 5) برومبت سياقي (system)
        system_prompt = build_main_prompt(
            analysis=user_analysis,
            answers=answers,
            personality=personality,
            previous_recommendation=previous_recommendation,
            ratings=ratings,
            lang=lang
        )

        # 6) بناء الرسائل
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # 6.1) ملخص طبقة Z + البروفايل المرمّز (system قصير)
        brief_lines = []
        if z:
            brief_lines.append(("محركات Z: " if lang == "العربية" else "Layer-Z: ") + ", ".join(z))
        brief_lines.append(_profile_brief(encoded_profile, lang))
        messages.append({"role": "system", "content": "\n".join(brief_lines)})

        # 6.2) سياق مختصر حول التوصيات والتقييمات
        if previous_recommendation:
            rec_join = "\n- " + "\n- ".join(map(str, previous_recommendation[:3]))
        else:
            rec_join = "\n- (no previous recs)"
        ratings_str = ", ".join(map(str, ratings[:3])) if ratings else "n/a"
        brief_context = (
            ("ملخص سياقي:\n" if lang == "العربية" else "Context brief:\n") +
            f"- Lang: {lang}\n"
            f"- Recommendations: {rec_join}\n"
            f"- Ratings: {ratings_str}\n"
        )
        messages.append({"role": "system", "content": brief_context})

        # 6.3) تاريخ المحادثة السابق (مختصر)
        for m in _trim_chat_history(chat_history or [], max_msgs=8):
            if m.get("role") in ("user", "assistant"):
                messages.append({"role": m["role"], "content": m.get("content", "")})

        # 6.4) رسالة المستخدم الحالية (أو سؤال توجيهي)
        if user_message:
            messages.append({"role": "user", "content": user_message})
        else:
            messages.append({
                "role": "user",
                "content": "أعد ضبط الخطة بخطوتين بسيطتين للأسبوع القادم." if lang == "العربية"
                else "Refine my weekly plan into two simple, immediate steps."
            })

        # 7) استدعاء نموذج الدردشة
        logging.info("Calling OpenAI chat completion...")
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=450
        )
        reply = (resp.choices[0].message.content or "").strip()

        # 8) تسجيل التفاعل
        try:
            log_user_insight(
                user_id=user_id,
                content={
                    "language": lang,
                    "answers": answers,
                    "ratings": ratings,
                    "user_analysis": user_analysis,
                    "previous_recommendation": previous_recommendation,
                    "personality_used": personality,
                    "user_message": user_message,
                    "ai_reply": reply,
                },
                event_type="chat_interaction"
            )
        except Exception as e:
            logging.warning(f"Logging failed: {e}")

        return reply if reply else (
            "✅ تم تحديث الخطة بخطوتين عمليتين. جرّب أول خطوة اليوم."
            if lang == "العربية" else
            "✅ Plan updated with two actionable steps. Try the first one today."
        )

    except Exception as e:
        logging.error(f"Dynamic chat failed: {e}")
        return (
            f"❌ حدث خطأ أثناء المحادثة الديناميكية: {e}"
            if lang == "العربية" else
            f"❌ Dynamic chat failed: {e}"
        )


# (اختياري) فحص صحة سريع
def healthcheck() -> Dict[str, Any]:
    return {
        "openai_key_set": bool(OPENAI_API_KEY),
        "model": CHAT_MODEL,
        "client_ready": client is not None
    }
