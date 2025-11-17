# core/followup_questions.py

import os
import json
import openai

from src.utils.user_analysis import load_user_analysis
from src.utils.chat_personality import get_chat_personality
from src.analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def start_dynamic_followup_chat(user_message, user_id, previous_recommendation, lang="العربية"):
    # تحميل السمات المحللة سابقًا
    traits = load_user_analysis(user_id)
    personality = get_chat_personality(user_id)

    # تحليل إضافي لتعليق المستخدم (Layer Z)
    layer_z_traits = analyze_silent_drivers(user_message)
    all_traits = list(set(traits + layer_z_traits))  # دمج وتحسين السمات

    # إعداد برومبت النظام
    if lang == "العربية":
        system_prompt = f"""
أنت {personality['name']}، مدرب ذكي يعمل ضمن نظام Sport Sync.
نبرتك: {personality['tone']}
أسلوبك: {personality['style']}
فلسفتك: {personality['philosophy']}
السمات المستخرجة: {', '.join(str(x) for x in all_traits)}

مهمتك: التفاعل مع المستخدم بذكاء.
❌ لا تكرر التوصية السابقة.
✅ اربط تعليقه بالتحليل وقدم توصية جديدة تعكس هويته الحقيقية.
"""
        user_prompt = f"""
📝 تعليق المستخدم: {user_message}
📌 التوصية السابقة: {previous_recommendation}

قدّم توصية بديلة أكثر دقة ووضح لماذا هي مناسبة له.
"""
    else:
        system_prompt = f"""
You are {personality['name']}, a smart coach working within the Sport Sync system.
Tone: {personality['tone']}
Style: {personality['style']}
Philosophy: {personality['philosophy']}
User traits: {', '.join(str(x) for x in all_traits)}

Your task is to respond intelligently to the user.
❌ Do not repeat the previous recommendation.
✅ Link their feedback to their previous analysis and suggest a better-fitting sport.
"""
        user_prompt = f"""
📝 User comment: {user_message}
📌 Previous recommendation: {previous_recommendation}

Please suggest a better, smarter sport and explain why.
"""

    # إرسال إلى GPT
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]
    )

    return response.choices[0].message.content.strip()