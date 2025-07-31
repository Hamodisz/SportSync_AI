import os
import openai
from core.shared_utils import generate_main_prompt
from core.user_logger import log_user_insight
from core.memory_cache import get_cached_personality
from core.user_analysis import analyze_user_from_answers
from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers

# إعداد عميل OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------------
# [1] توليد التوصيات الرياضية
# ------------------------------
def generate_sport_recommendation(answers, lang="العربية", user_id="N/A"):
    try:
        # تحليل المستخدم وبناء شخصيته
        user_analysis = analyze_user_from_answers(answers)

        # تحليل Layer Z - المحركات الصامتة
        silent_drivers = analyze_silent_drivers(answers, lang=lang)
        user_analysis["silent_drivers"] = silent_drivers

        # جلب الشخصية
        personality = get_cached_personality(user_analysis, lang=lang)

        # توليد البرومبت
        prompt = generate_main_prompt(
            analysis=user_analysis,
            answers=answers,
            personality=personality,
            lang=lang
        )

        # إرسال البرومبت إلى GPT
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=1000
        )

        full_response = completion.choices[0].message.content.strip()
        recs = split_recommendations(full_response)

        # حفظ سجل التوصية والتحليل
        log_user_insight(
            user_id=user_id,
            content={
                "answers": answers,
                "language": lang,
                "recommendations": recs,
                "raw_response": full_response,
                "user_analysis": user_analysis,
                "personality_used": personality,
            },
            event_type="initial_recommendation"
        )

        return recs

    except Exception as e:
        return [f"❌ حدث خطأ أثناء توليد التوصية: {str(e)}"]

# ------------------------------
# [2] تقسيم التوصيات الثلاثة
# ------------------------------
def split_recommendations(full_text):
    recs = []
    lines = full_text.splitlines()
    buffer = []

    for line in lines:
        if ("التوصية" in line or line.strip().startswith("1.")) and buffer:
            recs.append("\n".join(buffer).strip())
            buffer = [line]
        else:
            buffer.append(line)

    if buffer:
        recs.append("\n".join(buffer).strip())

    while len(recs) < 3:
        recs.append("⚠ لا توجد توصية.")

    return recs[:3]