# content_studio/generate_script/script_generator.py

import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Detect if using OpenRouter (keys start with sk-or-v1-)
api_key = os.getenv("OPENAI_API_KEY")
is_openrouter = api_key and api_key.startswith("sk-or-v1-")

# Try new OpenAI client (v1.x)
try:
    from openai import OpenAI
    if is_openrouter:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        client = OpenAI(api_key=api_key)
    USE_NEW_API = True
except ImportError:
    # Fallback to old API (v0.x)
    import openai
    openai.api_key = api_key
    if is_openrouter:
        openai.api_base = "https://openrouter.ai/api/v1"
    USE_NEW_API = False

def generate_script(topic: str, tone: str = "emotional", lang: str = "english") -> str:
    if lang.lower() == "arabic":
        prompt = f"""
اكتب لي سكربت قصير على شكل مشاهد لواجهة إفتتاحية ومُلهمة عن: {topic}
(السكربت يجب أن يحتوي على 6-4 مشاهد وكل مشهد في سطرين فقط)

خلي الرد مؤثر ويلمس المشاعر، ويكون مناسب لتحويله إلى فيديو تحفيزي قصير
"""
    else:
        prompt = f"""
Write a short video script in scene format about: {topic}
Use a {tone} tone, make it deep, human, and emotionally engaging.

The script should be 4 to 6 short scenes (1–2 lines each) in clear English.
Make it visually expressive to convert into a short video later.
"""

    if USE_NEW_API:
        # New OpenAI API (v1.x)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    else:
        # Old OpenAI API (v0.x)
        import openai
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()


def generate_multiple_scripts(topics, tone="emotional", lang="english", output_path="data/video_scripts.json"):
    results = []
    for i, topic in enumerate(topics, 1):
        print(f"🎬 Generating script {i}/{len(topics)}: {topic}")
        script = generate_script(topic, tone=tone, lang=lang)
        results.append({"topic": topic, "script": script})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ All scripts saved to {output_path}")


if __name__ == "__main__":
    # تقدر تعدل المواضيع هنا حسب خطة اليوم
    topics = [
        "The hidden power of staying silent",
        "Why discipline is more loving than motivation",
        "Your future self is begging you to change",
        "What sport teaches you about life better than school",
        "The most underrated muscle in your body"
    ]

    generate_multiple_scripts(topics, tone="emotional", lang="english")
