# -- coding: utf-8 --
"""
content_studio/ai_images/generate_images.py

مولّد صور للمشاهد مع خيار تجاوز OpenAI تمامًا وإنشاء صور Placeholder محليًا.
الدالة العامة التي يستدعيها المشروع هي: generate_images(script_text, lang="ar")

افتراضيًا: نستخدم Placeholder (USE_IMAGE_PLACEHOLDERS=1).
لتفعيل OpenAI لاحقًا: ضع USE_IMAGE_PLACEHOLDERS=0 ووفّر OPENAI_API_KEY وحساب/منظمة مُوثّقة.
"""

import os
import re
import base64
import logging
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

# ================== إعداد اللوجينغ ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | ai_images | %(message)s",
)

# ================== إعدادات ومسارات ==================
OUTPUT_DIR = Path("content_studio/ai_images/outputs/")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ✅ افتراضيًا نفعل الـ Placeholder. يمكن قلبه بمتغير بيئة لاحقًا.
SEED_PLACEHOLDERS: bool = os.getenv("USE_IMAGE_PLACEHOLDERS", "1").lower() in ("1", "true", "yes")

# إن أردت استخدام OpenAI Images لاحقًا، اضبط USE_IMAGE_PLACEHOLDERS=0
# وسنحاول تهيئة OpenAI. إذا فشل نرجع تلقائيًا للـ Placeholder.
client = None
if not SEED_PLACEHOLDERS:
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
        from openai import OpenAI  # type: ignore

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.warning("OPENAI_API_KEY غير مضبوط؛ سنستخدم صور Placeholder.")
            SEED_PLACEHOLDERS = True
        else:
            client = OpenAI(api_key=api_key)
            logging.info("✅ OpenAI client جاهز.")
    except Exception as e:
        logging.warning(f"تعذّر تهيئة OpenAI ({e})؛ سنستخدم صور Placeholder.")
        SEED_PLACEHOLDERS = True
        client = None


# ================== أدوات مساعدة ==================
def _wrap_lines(text: str, max_len: int = 26) -> List[str]:
    """لفّ نص بسيط للسطر."""
    words = text.split()
    out, line = [], ""
    for w in words:
        if len((line + " " + w).strip()) <= max_len:
            line = (line + " " + w).strip()
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def _draw_placeholder(text: str, idx: int, size=(1024, 1024)) -> str:
    """إنشاء صورة نصّية محليًا (Placeholder) وتمييز رقم المشهد."""
    img = Image.new("RGB", size, (20, 24, 28))
    draw = ImageDraw.Draw(img)

    # جرّب خط نظام، وإن فشل استخدم الافتراضي
    try:
        font_big = ImageFont.truetype("arial.ttf", 64)
        font_body = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font_big = ImageFont.load_default()
        font_body = ImageFont.load_default()

    # عنوان بسيط
    draw.text((40, 40), f"Scene {idx+1}", fill=(245, 245, 245), font=font_big)

    # نص المشهد ملفوف
    y = 140
    for line in _wrap_lines(text, max_len=30)[:12]:
        draw.text((40, y), line, fill=(220, 220, 220), font=font_body)
        y += 52

    out = OUTPUT_DIR / f"scene_{idx+1}.png"
    img.save(out, format="PNG")
    return str(out)


def extract_scenes(script_text: str) -> List[str]:
    """
    استخراج المشاهد من سكربت عربي/إنجليزي:
      - Scene #1: ... / Scene: ...
      - مشهد 1: ... / مشهد: ...
      - أو تقسيم على الأسطر الفارغة كخطة احتياطية.
    """
    parts = re.split(
        r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
        script_text,
        flags=re.IGNORECASE,
    )
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script_text) if p.strip()]
    # فيديوهات قصيرة: حد أعلى 6 مشاهد
    return scenes[:6] if scenes else [script_text.strip()[:140]]


def _save_png_from_b64(b64_data: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(b64_data))


# ================== نواة توليد صورة لمشهد (OpenAI اختياري) ==================
def _generate_openai_image(prompt: str, idx: int, size: str = "1024x1024") -> str:
    """
    توليد صورة عبر OpenAI (عند توافره). سيرفع استثناء لو فشل (نعود للـ Placeholder).
    ملاحظة: يلزم حساب/منظمة مُوثّقة لنموذج gpt-image-1.
    """
    if client is None:
        raise RuntimeError("OpenAI client غير جاهز")

    style_suffix = "\nStyle: cinematic, realistic, dramatic lighting, high detail."
    full_prompt = prompt.strip() + style_suffix

    resp = client.images.generate(
        model="gpt-image-1",
        prompt=full_prompt,
        size=size,
        quality="standard",  # لا تغيّرها هنا
        n=1,
    )
    b64_img = resp.data[0].b64_json
    out_path = OUTPUT_DIR / f"scene_{idx+1}.png"
    _save_png_from_b64(b64_img, out_path)
    return str(out_path)


# ================== واجهات رئيسية ==================
def generate_image_for_scene(
    scene_description: str,
    index: int,
    image_style: str = "cinematic realistic, dramatic lighting, high detail",
    size: str = "1024x1024",
) -> str:
    """
    يولّد صورة واحدة لمشهد.
    الأولوية: Placeholder محلي إذا كان SEED_PLACEHOLDERS=True،
    وإلا جرّب OpenAI ثم ارجع للـ Placeholder عند أي خطأ.
    """
    if SEED_PLACEHOLDERS:
        w, h = [int(x) for x in size.split("x")]
        return _draw_placeholder(scene_description, index, size=(w, h))

    try:
        prompt = f"{scene_description}. Style: {image_style}."
        return _generate_openai_image(prompt, idx=index, size=size)
    except Exception as e:
        logging.warning(f"[Images] فشل OpenAI ({e}) — نرجع لـ Placeholder.")
        w, h = [int(x) for x in size.split("x")]
        return _draw_placeholder(scene_description, index, size=(w, h))


def generate_images_from_script(
    script_text: str,
    image_style: str = "cinematic realistic",
    size: str = "1024x1024",
) -> List[str]:
    # تنظيف مجلد الإخراج
    for f in OUTPUT_DIR.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

    scenes = extract_scenes(script_text)
    paths: List[str] = []
    for i, scene in enumerate(scenes):
        logging.info(f"🎨 Generating image for scene #{i+1}…")
        p = generate_image_for_scene(scene_description=scene, index=i, image_style=image_style, size=size)
        paths.append(p)
    return paths


def generate_images(script_text: str, lang: str = "ar") -> List[str]:
    """
    واجهة موحّدة يستدعيها core_engine.
    """
    style = "cinematic realistic, soft contrast, mood lighting, depth of field"
    return generate_images_from_script(script_text, image_style=style, size="1024x1024")
