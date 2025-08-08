# content_studio/generate_script/script_generator.py
# -- coding: utf-8 --

import os
import json
from typing import List
from openai import OpenAI

# ✅ تأكد من وجود مفتاح API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY غير مُعرّف في المتغيرات البيئية. "
        "ضِف المفتاح ثم أعد التشغيل."
    )

client = OpenAI(api_key=OPENAI_API_KEY)

def _build_prompt(topic: str, tone: str, lang: str) -> str:
    lang = (lang or "").lower()
    if lang in ("ar", "arabic", "arab"):
        return f"""اكتب سكربت قصير بصيغة مشاهد، مُلهِم وافتتاحي عن: {topic}
- 4 إلى 6 مشاهد
- كل مشهد سطرين كحد أقصى
- لغة عربية واضحة ومؤثرة
- مناسب للتحويل لفيديو قصير تحفيزي
- اسلوب: {tone}"""
    else:
        return f"""Write a short video script as scenes about: {topic}
- 4 to 6 scenes
- 1–2 lines per scene
- Visually expressive and easy to turn into a short video
- Tone: {tone}"""

def generate_script(topic: str, tone: str = "emotional", lang: str = "ar") -> str:
    """
    يولّد سكربت قصير بصيغة مشاهد باستخدام OpenAI Chat Completions.
    """
    prompt = _build_prompt(topic, tone, lang)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",      # غيّره إلى gpt-4o إذا تبغى أعلى جودة
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )

    content = resp.choices[0].message.content or ""
    return content.strip()

def generate_multiple_scripts(
    topics: List[str],
    tone: str = "emotional",
    lang: str = "ar",
    output_path: str = "data/video_scripts.json"
) -> None:
    """
    يولّد عدة سكربتات ويحفظها في JSON.
    """
    results = []
    for i, topic in enumerate(topics, 1):
        print(f"🎬 Generating script {i}/{len(topics)}: {topic}")
        script = generate_script(topic, tone=tone, lang=lang)
        results.append({"topic": topic, "script": script})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ All scripts saved to {output_path}")

if _name_ == "_main_":
    # مثال تشغيل مباشر
    topics = [
        "قوة البداية الصغيرة في حياتك الرياضية",
        "كيف تغيّر 10 دقائق يوميًا لياقتك",
        "الانضباط أهم من الدافع اللحظي",
        "لماذا الرياضة أذكى استثمار في ذاتك"
    ]
    generate_multiple_scripts(topics, tone="emotional", lang="ar")
