import os
import hashlib
from typing import List
from openai import OpenAI
import requests

# ✅ إعداد عميل OpenAI مع مفتاح من environment
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ✅ مجلد الحفظ
OUTPUT_DIR = "generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _sanitize_filename(text: str) -> str:
    """توليد اسم ملف فريد من النص باستخدام hash"""
    return hashlib.md5(text.encode()).hexdigest()[:10]

def generate_images_from_script(script_text: str, style: str = "cinematic", resolution: str = "1024x1024") -> List[str]:
    """
    توليد صور لكل مشهد من السكربت باستخدام DALL·E أو نموذج vision قوي
    """
    sentences = [s.strip() for s in script_text.split(".") if s.strip()]
    image_paths = []

    for i, sentence in enumerate(sentences):
        prompt = f"{style} illustration of: {sentence}"
        filename = f"{_sanitize_filename(sentence)}.png"
        file_path = os.path.join(OUTPUT_DIR, filename)

        # ✅ تجنب التكرار
        if os.path.exists(file_path):
            image_paths.append(file_path)
            continue

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=resolution,
                quality="standard",
                n=1
            )
            image_url = response.data[0].url

            # ✅ تحميل الصورة
            image_data = requests.get(image_url).content
            with open(file_path, "wb") as f:
                f.write(image_data)

            image_paths.append(file_path)

        except Exception as e:
            print(f"❌ Failed generating image for: {sentence}\n{e}")
            continue

    return image_paths
