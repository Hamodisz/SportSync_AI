# script_generator.py

import openai

# إعداد API (حط مفتاحك أو استورده من متغيرات البيئة)
client = openai.OpenAI(api_key="your-api-key-here")  # استبدل بـ os.getenv(...) إذا كنت تستخدم env

def generate_script(topic: str, tone: str = "emotional", lang: str = "english") -> str:
    """
    يولد سكربت مرئي بصيغة مشاهد بناءً على موضوع ونبرة.
    """
    if lang.lower() == "arabic":
        prompt = f"""
اكتب لي سكربت قصير على شكل مشاهد، بلهجة إنسانية وعاطفية، عن: {topic}
السكربت يجب أن يحتوي على 4–6 مشاهد، وكل مشهد يبدأ بـ (المشهد #1: ...)

خلي السرد مؤثر ويلامس المشاعر، ويكون مناسب لتحويله إلى فيديو تعليمي قصير.
"""
    else:
        prompt = f"""
Write a short video script in scene format about: {topic}
Use a {tone} tone, make it deep, human, and emotionally engaging.
Start each part with "Scene #1: ..." and create 4–6 scenes max.
Make it suitable for converting into a visual + voice video.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )

    return response.choices[0].message.content.strip()

# تشغيل تجريبي عند تشغيل الملف مباشرة (اختياري)
if _name_ == "_main_":
    topic = "Why do people quit sports after two weeks?"
    script = generate_script(topic)
    print(script)
