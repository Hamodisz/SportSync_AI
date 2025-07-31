import openai
import os
from core.user_analysis import apply_all_analysis_layers
from core.shared_utils import build_main_prompt, build_dynamic_personality
from core.user_logger import log_user_insight
from core.memory_cache import get_cached_personality, save_cached_personality
from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# 🧠 المحادثة التفاعلية الذكية
# -------------------------------
def start_dynamic_chat(answers, previous_recommendation, ratings, user_id, lang="العربية", chat_history=None, user_message=""):
    try:
        chat_history = chat_history or []

        # [1] التحليل الكامل للمستخدم
        user_analysis = apply_all_analysis_layers(str(answers))

        # [2] تحليل Layer Z (المحركات الصامتة)
        silent_drivers = analyze_silent_drivers(answers, lang=lang)
        user_analysis["silent_drivers"] = silent_drivers

        # [3] بناء أو جلب شخصية المدرب
        cache_key = f"{lang}_{hash(str(user_analysis))}"
        personality = get_cached_personality(user_analysis, lang)
        if not personality:
            personality = build_dynamic_personality(user_analysis, lang)
            save_cached_personality(cache_key, personality)

        # [4] بناء البرومبت السياقي الأولي
        messages = []
        intro_prompt = build_main_prompt(
            analysis=user_analysis,
            answers=answers,
            personality=personality,
            previous_recommendation=previous_recommendation,
            ratings=ratings,
            lang=lang
        )
        messages.append({"role": "system", "content": intro_prompt})

        # [5] تضمين سجل المحادثة السابق
        for entry in chat_history:
            messages.append({"role": entry["role"], "content": entry["content"]})

        # [6] إضافة رسالة المستخدم الحالية
        if user_message:
            messages.append({"role": "user", "content": user_message})

        # [7] إرسال إلى GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.9
        )

        reply = response.choices[0].message.content.strip()

        # [8] حفظ التفاعل في السجل
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
                "full_chat": chat_history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": reply}]
            },
            event_type="chat_interaction"
        )

        return reply

    except Exception as e:
        return f"❌ حدث خطأ أثناء المحادثة الديناميكية: {str(e)}"