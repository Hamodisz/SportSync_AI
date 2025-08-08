# content_studio/ai_images/generate_images.py
# -- coding: utf-8 --

import os
import re
import base64
from pathlib import Path
from io import BytesIO
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

# حمّل متغيرات البيئة (يدعم .env)
load_dotenv()

# انشاء عميل OpenAI بالطريقة الصحيحة
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY غير مضبوط. ضعه في متغيرات البيئة أو داخل ملف .env"
    )
client = OpenAI(api_key=OPENAI_API_KEY)

# مجلد الإخراج
OUTPUT_DIR = Path("content_studio/ai_images/outputs/")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------- أدوات مساعدة ---------
def extract_scenes(script_text: str) -> List[str]:
    """
    يحاول استخراج المشاهد من سكربت عربي/إنجليزي.
    يقبل صيغ مثل:
      - Scene #1: ...
      - مشهد 1: ...
      - أو يقسم على الأسطر الفارغة كخطة احتياطية
    """
    scenes = re.split(r"(?:Scene\s*#?\d+[:\-]?)|(?:مشهد\s*\d+[:\-]?)",
                      script_text, flags=re.IGNORECASE)
    scenes = [s.strip() for s in scenes if s and s.strip()]
    if not scenes:
        # تقسيم احتياطي على الأسطر الفارغة
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script_text) if p.strip()]
    return scenes


def _save_png_from_b64(b64_data: str, out_path: Path) -> None:
    img_bytes = base64.b64decode(b64_data)
    with open(out_path, "wb") as f:
        f.write(img_bytes)


# --------- توليد صورة لمشهد واحد ---------
def generate_image_for_scene(
    scene_description: str,
    image_style: str = "cinematic realistic, dramatic lighting, high detail",
    index: int = 0,
    size: str = "1024x1024"
) -> str:
    """
    يولّد صورة واحدة لمشهد باستخدام gpt-image-1 (واجهة الصور الحديثة).
    """
    full_prompt = f"{scene_description}. Style: {image_style}."

    resp = client.images.generate(
        model="gpt-image-1",        # استخدم النموذج الحديث للصور
        prompt=full_prompt,
        size=size,
        n=1,
        quality="standard"
    )

    # مخرجات واجهة الصور الحديثة تكون base64 وليس URL
    b64_img = resp.data[0].b64_json
    out_path = OUTPUT_DIR / f"scene_{index + 1}.png"
    _save_png_from_b64(b64_img, out_path)

    return str(out_path)


# --------- توليد صور لكل مشاهد السكربت ---------
def generate_images_from_script(
    script_text: str,
    image_style: str = "cinematic realistic",
    size: str = "1024x1024"
) -> List[str]:
    scenes = extract_scenes(script_text)
    image_paths: List[str] = []

    for i, scene in enumerate(scenes):
        print(f"🎨 Generating image for Scene #{i+1}...")
        path = generate_image_for_scene(
            scene_description=scene,
            image_style=image_style,
            index=i,
            size=size
        )
        image_paths.append(path)

    return image_paths


# --------- واجهة متوافقة مع بقية المشروع ---------
def generate_images(script_text: str, lang: str = "ar") -> List[str]:
    """
    دالة واجهة قياسية يستدعيها core_engine/المشروع.
    تتجاهل lang حالياً (ممكن تستخدمه لاحقاً لتخصيص الـ prompt).
    """
    # اختر ستايل افتراضي أنسب للفيديوهات التحفيزية
    style = "cinematic realistic, soft contrast, mood lighting, depth of field"
    return generate_images_from_script(script_text, image_style=style, size="1024x1024")


# --------- تشغيل مباشر للاختبار ---------
if _name_ == "_main_":
    from content_studio.generate_script.script_generator import generate_script
    test_script = generate_script("Why do people quit sports?", tone="emotional", lang="english")
    paths = generate_images_from_script(test_script, image_style="cinematic realistic")
    print("✅ Generated images:", paths)
