# -- coding: utf-8 --
"""
core/dynamic_chat.py
--------------------
محادثة تفاعلية ديناميكية مع المدرب الذكي، مدموجة مع:
- تحليل المستخدم عبر طبقات التحليل
- طبقة Z
- ترميز الإجابات إلى بروفايل سريع
- شخصية مدرّب ديناميكية مع كاش
- تسجيل الأثر (user_logger + DataPipe)
- قراءة الإعدادات من data/app_config.json (model/temperature/max_tokens/..)

ملاحظات:
- تعتمد على طبقة llm_client.py (OpenAI/Groq… عبر واجهة واحدة).
- تدعم العربية والإنجليزية.
- تحافظ على سجل المحادثة مختصر لتقليل التكلفة.
"""

from __future__ import annotations

import os
import json
import logging
import math
from typing import List, Dict, Any, Optional, Generator

# ============== إعداد اللوجينغ ==============
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | dynamic_chat | %(message)s"
)

# ============== App Config ==============
try:
    from core.app_config import get_config
    CFG = get_config()
except Exception as e:
    logging.warning(f"app_config unavailable: {e}")
    CFG = {}

def _cfg_chat() -> Dict[str, Any]:
    """قراءة حية لإعدادات المحادثة من الكونفيج (تتحدّث أثناء التشغيل)."""
    cfg = get_config() if 'get_config' in globals() else (CFG or {})
    chat = (cfg.get("chat") or {})
    llm  = (cfg.get("llm") or {})
    return {
        "model": llm.get("model", os.getenv("CHAT_MODEL", "gpt-4o-mini")),
        "temperature": float(chat.get("temperature", 0.8)),
        "max_tokens": int(chat.get("max_tokens", 450)),
        "stream_temperature": float(chat.get("stream_temperature", chat.get("temperature", 0.8))),
        "app_version": cfg.get("app_version", "dev")
    }

# ============== LLM Client (موحّد) ==============
try:
    from core.llm_client import make_llm_client, pick_models, chat_once
except Exception as e:
    raise RuntimeError("llm_client.py مفقود أو غير متاح — لازم يكون ضمن core/") from e

LLM_CLIENT = make_llm_client()
try:
    CHAT_MODEL_MAIN, CHAT_MODEL_FALLBACK = pick_models()  # يُفضّل استخدام ما يجي من pick_models
except Exception:
    CHAT_MODEL_MAIN, CHAT_MODEL_FALLBACK = None, None

# ============== Telemetry (DataPipe) ==============
try:
    from core.data_pipe import get_pipe
    _PIPE = get_pipe()
except Exception as e:
    logging.info(f"DataPipe unavailable ({e})")
    _PIPE = None

# ============== استيرادات من مشروعك ==============
# طبقات التحليل + طبقة Z
try:
    from analysis.user_analysis import analyze_user_from_answers as _ua
    def apply_all_analysis_layers(text: str, user_id: str = "web_user", lang: str = "العربية") -> Dict[str, Any]:
        try:
            answers = json.loads(text) if text and text.strip().startswith("{") else {"_raw": text or ""}
        except Exception:
            answers = {"_raw": text or ""}
        try:
            traits = _ua(user_id=user_id, answers=answers, lang=lang)
        except Exception as e:
            logging.info(f"user_analysis fallback: {e}")
            traits = []
        return {
            "quick_profile": " | ".join(map(str, (traits if isinstance(traits, list) else list(traits.values()) if isinstance(traits, dict) else [])[:6])) if traits else "fallback",
            "raw": answers,
            "traits": traits
        }
except Exception as e:
    logging.info(f"Using minimal analysis fallback ({e}).")
    def apply_all_analysis_layers(text: str, user_id: str = "web_user", lang: str = "العربية") -> Dict[str, Any]:
        return {"quick_profile": "fallback", "raw": text, "traits": []}

try:
    from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception as e:
    logging.info(f"Fallback: analyze_silent_drivers غير متاحة ({e}).")
    def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
        return ["انجازات سريعة", "تفضيل تحديات قصيرة", "ميول فردية"]

# ترميز الإجابات إلى بروفايل (scores/prefs/signals/axes/z_markers...)
try:
    from core.answers_encoder import encode_answers
except Exception as e:
    logging.info(f"Fallback: answers_encoder غير متاح ({e}). سيتم استخدام بروفايل مبسط.")
    def encode_answers(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
        return {
            "lang": lang,
            "scores": {},
            "axes": {},
            "z_markers": [],
            "prefs": {"time_block": "medium", "budget_hint": "med", "environment_pref": "mixed"},
            "signals": [],
            "vr_inclination": 0
        }

# بناء البرومبت والشخصية
try:
    from core.shared_utils import build_main_prompt, build_dynamic_personality
except Exception:
    logging.info("Using built-in minimal coach persona / prompt templates.")
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
                "طابق الأسلوب مع شخصية المدرب التالية: " + str(personality) + " "
                "لديك تحليل المستخدم ونتائج طبقة Z وإجابات الاستبيان وتقييماته. "
                "اكتب ردودًا قصيرة وعملية تُعدّل الخطة فورًا حسب ملاحظات المستخدم، بدون لوم."
            )
        else:
            return (
                "You are a professional AI coach from SportSync AI. "
                "Use a clear, respectful, motivating tone. "
                "Match the style with this coach personality: " + str(personality) + " "
                "You have the user's analysis, Layer-Z drivers, survey answers and ratings. "
                "Write concise, actionable guidance and adapt the plan immediately based on feedback."
            )

# التخزين المؤقت للشخصية + التسجيل
try:
    from core.memory_cache import get_cached_personality, save_cached_personality
except Exception as e:
    logging.info(f"Fallback: memory_cache غير متاحة ({e}). سيتم استخدام ذاكرة داخلية مؤقتة.")
    _MEM_CACHE: Dict[str, str] = {}
    def get_cached_personality(cache_key: str) -> Optional[str]:
        return _MEM_CACHE.get(cache_key)
    def save_cached_personality(cache_key: str, value: str) -> None:
        _MEM_CACHE[cache_key] = value

try:
    from core.user_logger import log_user_insight
except Exception as e:
    logging.info(f"Fallback: user_logger غير متاحة ({e}). سيتم الطباعة للكونسول بدل التسجيل.")
    def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "chat_interaction") -> None:
        logging.info(f"[LOG:{event_type}] {user_id} -> {list(content.keys())}")

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
    try:
        for k, v in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:5]:
            top_scores.append(f"{k}:{v}")
    except Exception:
        pass
    if lang == "العربية":
        return (
            "ملخص بروفايل مرمّز:\n"
            f"- إشارات: {', '.join(str(x) for x in signals) if signals else 'n/a'}\n"
            f"- أعلى الدرجات: {', '.join(str(x) for x in top_scores) if top_scores else 'n/a'}\n"
            f"- تفضيلات: وقت={prefs.get('time_block','n/a')}, ميزانية={prefs.get('budget_hint','n/a')}, بيئة={prefs.get('environment_pref','n/a')}\n"
        )
    else:
        return (
            "Encoded profile brief:\n"
            f"- Signals: {', '.join(str(x) for x in signals) if signals else 'n/a'}\n"
            f"- Top scores: {', '.join(str(x) for x in top_scores) if top_scores else 'n/a'}\n"
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
        if not LLM_CLIENT:
            return "❌ لا يمكن تشغيل المحادثة: عميل LLM غير مهيأ."

        # إعدادات المحادثة الحية من الكونفيج
        C = _cfg_chat()
        CHAT_MODEL = CHAT_MODEL_MAIN or C["model"]
        TEMP = C["temperature"]
        MAXTOK = C["max_tokens"]

        # 1) ترميز الإجابات أولًا (Z-axes/Z-markers/scores)
        try:
            encoded = encode_answers(answers, lang=lang)
            if not isinstance(encoded, dict):
                encoded = {"scores": {}, "axes": {}, "z_markers": [], "prefs": {}, "signals": []}
        except Exception as e:
            logging.warning(f"answers_encoder failed: {e}")
            encoded = {"scores": {}, "axes": {}, "z_markers": [], "prefs": {}, "signals": []}

        # 2) تحليل المستخدم الكامل
        user_analysis = apply_all_analysis_layers(_safe_json(answers), user_id=user_id, lang=lang)

        # 3) ضمّ البروفايل المرمّز داخل التحليل
        user_analysis["encoded_profile"] = encoded
        user_analysis["z_scores"] = encoded.get("scores", {})
        user_analysis["z_axes"] = encoded.get("axes", {})
        user_analysis["z_markers"] = encoded.get("z_markers", [])

        # 4) طبقة Z
        try:
            z = analyze_silent_drivers(answers, lang=lang) or []
        except Exception as e:
            logging.warning(f"Layer Z failed: {e}")
            z = []
        user_analysis["silent_drivers"] = z

        # 5) شخصية المدرب مع كاش
        cache_key = f"{lang}:{hash(_safe_json({'ua': user_analysis.get('quick_profile',''), 'scores': encoded.get('scores', {}), 'prefs': encoded.get('prefs', {})}))}"
        personality = get_cached_personality(cache_key)
        if not personality:
            personality = build_dynamic_personality(user_analysis, lang)
            save_cached_personality(cache_key, personality)

        # 6) برومبت سياقي (system)
        system_prompt = build_main_prompt(
            analysis=user_analysis,
            answers=answers,
            personality=personality,
            previous_recommendation=previous_recommendation,
            ratings=ratings,
            lang=lang
        )

        # 7) بناء الرسائل
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # 7.1) ملخص طبقة Z + البروفايل المرمّز (system قصير)
        brief_lines = []
        if z:
            brief_lines.append(("محركات Z: " if lang == "العربية" else "Layer-Z: ") + ", ".join(str(x) for x in z))
        brief_lines.append(_profile_brief(encoded, lang))
        messages.append({"role": "system", "content": "\n".join(str(x) for x in brief_lines)})

        # 7.2) سياق مختصر حول التوصيات والتقييمات + Z-axes/Z-markers
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
        try:
            brief_context += (
                f"- Z-axes: {json.dumps(encoded.get('axes', {}), ensure_ascii=False)}\n"
                f"- Z-markers: {', '.join(str(x) for x in encoded.get('z_markers', []))}\n"
            )
        except Exception:
            pass
        messages.append({"role": "system", "content": brief_context})

        # 7.3) تاريخ المحادثة السابق (مختصر)
        for m in _trim_chat_history(chat_history or [], max_msgs=8):
            if m.get("role") in ("user", "assistant"):
                messages.append({"role": m["role"], "content": m.get("content", "")})

        # 7.4) رسالة المستخدم الحالية (أو سؤال توجيهي)
        if user_message:
            messages.append({"role": "user", "content": user_message})
        else:
            messages.append({
                "role": "user",
                "content": "أعد ضبط الخطة بخطوتين بسيطتين للأسبوع القادم." if lang == "العربية"
                else "Refine my weekly plan into two simple, immediate steps."
            })

        # 8) استدعاء النموذج عبر طبقة llm_client
        logging.info(f"Calling LLM (model={CHAT_MODEL})...")
        reply = chat_once(
            client=LLM_CLIENT,
            model=CHAT_MODEL,
            messages=messages,
            temperature=TEMP,
            timeout_s=30,
            max_tokens=MAXTOK
        )
        reply = (reply or "").strip()

        # 9) تسجيل التفاعل (user_logger + DataPipe)
        payload_log = {
            "language": lang,
            "answers": answers,
            "ratings": ratings,
            "user_analysis": user_analysis,
            "previous_recommendation": previous_recommendation,
            "personality_used": personality,
            "user_message": user_message,
            "ai_reply": reply,
        }
        try:
            log_user_insight(user_id=user_id, content=payload_log, event_type="chat_interaction")
        except Exception as e:
            logging.warning(f"Logging failed: {e}")

        if _PIPE:
            try:
                _PIPE.send(
                    event_type="chat_interaction",
                    payload=payload_log,
                    user_id=user_id,
                    lang=lang,
                    model=CHAT_MODEL
                )
            except Exception as e:
                logging.info(f"DataPipe send failed: {e}")

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


# ============== بثّ حي (Streaming) ==============
def start_dynamic_chat_stream(
    answers: Dict[str, Any],
    previous_recommendation: List[str],
    ratings: List[int],
    user_id: str,
    lang: str = "العربية",
    chat_history: Optional[List[Dict[str, str]]] = None,
    user_message: str = ""
) -> Generator[str, None, None]:
    """
    توليد ردّ المساعد ببث حي (stream). إذا ما توفر ستريم حقيقي في llm_client،
    سنحاكيه بتقطيع الردّ النهائي إلى أجزاء صغيرة.
    """
    # نبني نفس الرسائل ثم نستخدم chat_once ونقسّم الناتج على دفعات
    text = start_dynamic_chat(
        answers=answers,
        previous_recommendation=previous_recommendation,
        ratings=ratings,
        user_id=user_id,
        lang=lang,
        chat_history=chat_history,
        user_message=user_message
    )
    # محاكاة بث: تقسيم النص chunks
    chunk_size = 48
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]


# (اختياري) فحص صحة سريع
def healthcheck() -> Dict[str, Any]:
    C = _cfg_chat()
    return {
        "llm_client_ready": bool(LLM_CLIENT),
        "model_main": CHAT_MODEL_MAIN or C["model"],
        "model_fallback": CHAT_MODEL_FALLBACK or "",
        "temperature": C["temperature"],
        "max_tokens": C["max_tokens"],
        "app_version": C["app_version"]
    }
