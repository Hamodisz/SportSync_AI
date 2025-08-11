# -- coding: utf-8 --
"""
content_studio/ai_images/generate_images.py

توليد صور المشاهد بدون OpenAI:
- يحاول أولاً Diffusers (Stable Diffusion v1-5) محليًا (CPU/GPU).
- إن تعذّر: ينسخ من مجلدات عينات (generated_images / sample_assets/images / assets/samples).
- إن لم يجد: يولّد صور Placeholder نصّية بـ PIL.
الدالة العامة التي يستدعيها المشروع: generate_images(script_text, lang="ar")
"""

from _future_ import annotations

import os
import re
import logging
from pathlib import Path
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | ai_images | %(message)s"
)

# مسارات إخراج و عينات
OUTPUT_DIR = Path("content_studio/ai_images/outputs/")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_DIRS = [
    Path("generated_images"),
    Path("sample_assets/images"),
    Path("assets/samples"),
]

# ---------------- Diffusers (Stable Diffusion) ----------------
USE_DIFFUSERS = False
sd_pipe = None
device = "cpu"
model_id = os.getenv("SD_MODEL_ID", "runwayml/stable-diffusion-v1-5")  # نموذج خفيف ومجاني

try:
    from diffusers import StableDiffusionPipeline
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"[Diffusers] Loading model: {model_id} on {device} (first time may take a while)")
    sd_pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=(torch.float16 if device == "cuda" else torch.float32),
        safety_checker=None,
    )
    sd_pipe = sd_pipe.to(device)
    if device == "cpu":
        try:
            sd_pipe.enable_attention_slicing()
        except Exception:
            pass
    USE_DIFFUSERS = True
    logging.info("[Diffusers] Ready.")
except Exception as e:
    logging.info(f"[Diffusers] Not available, will use fallbacks. ({e})")
    USE_DIFFUSERS = False
    sd_pipe = None

# ---------------- PIL placeholders ----------------
from PIL import Image, ImageDraw, ImageFont


def extract_scenes(script_text: str) -> List[str]:
    """تجزئة السكربت إلى مشاهد (عربي/إنجليزي) مع حد أقصى 6 مشاهد افتراضيًا."""
    parts = re.split(
        r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
        script_text,
        flags=re.IGNORECASE,
    )
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script_text) if p.strip()]
    return scenes[:6] if scenes else [script_text.strip()[:140]]


def _copy_from_samples(idx: int) -> Optional[str]:
    """نسخ صورة من مجلدات عينات إن وجدت."""
    for d in SAMPLE_DIRS:
        if not d.exists():
            continue
        candidates = sorted(
            list(d.glob(".png")) + list(d.glob(".jpg")) + list(d.glob("*.jpeg"))
        )
        if not candidates:
            continue
        src = candidates[idx % len(candidates)]
        dst = OUTPUT_DIR / f"scene_{idx+1}{src.suffix.lower()}"
        Image.open(src).save(dst)
        return str(dst)
    return None


def _wrap_lines(text: str, max_len: int = 28) -> List[str]:
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len((line + " " + w).strip()) <= max_len:
            line = (line + " " + w).strip()
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def _make_placeholder(text: str, idx: int, size=(512, 512)) -> str:
    """توليد صورة نصية بسيطة كمكان-holder."""
    img = Image.new("RGB", size, (26, 28, 34))
    d = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("arial.ttf", 36)
        font_body = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font_big = ImageFont.load_default()
        font_body = ImageFont.load_default()
    d.text((20, 20), f"Scene {idx+1}", fill=(235, 235, 235), font=font_big)
    y = 80
    for ln in _wrap_lines(text, max_len=32)[:10]:
        d.text((20, y), ln, fill=(220, 220, 220), font=font_body)
        y += 30
    out = OUTPUT_DIR / f"scene_{idx+1}.png"
    img.save(out, format="PNG")
    return str(out)


def _sd_generate(prompt: str, idx: int, image_size: int = 512, steps: int = 20, guidance: float = 7.0) -> str:
    """توليد صورة بموديل Stable Diffusion عبر Diffusers."""
    if not (USE_DIFFUSERS and sd_pipe is not None):
        raise RuntimeError("Diffusers not available")

    clean_prompt = f"{prompt}. cinematic, realistic, detailed, soft lighting, depth of field, high quality"
    image = sd_pipe(
        prompt=clean_prompt,
        num_inference_steps=steps if device == "cpu" else max(25, steps),
        guidance_scale=guidance,
        height=image_size,
        width=image_size,
    ).images[0]

    out = OUTPUT_DIR / f"scene_{idx+1}.png"
    image.save(out)
    return str(out)


def generate_image_for_scene(
    scene_description: str,
    index: int,
    image_style: str = "cinematic, realistic, soft lighting, high detail",
    size: str = "512x512",
) -> str:
    """أولوية التوليد: Diffusers → عينات → Placeholder."""
    try:
        if USE_DIFFUSERS and sd_pipe is not None:
            try:
                w, h = size.split("x")
                size_px = int(w)  # نفترض مربع
            except Exception:
                size_px = 512
            return _sd_generate(
                prompt=f"{scene_description}. Style: {image_style}",
                idx=index,
                image_size=size_px,
            )
        raise RuntimeError("Diffusers disabled or not loaded")
    except Exception as e:
        logging.info(f"[Images] Diffusers unavailable: {e}. Trying samples/placeholder…")
        from_samples = _copy_from_samples(index)
        if from_samples:
            return from_samples
        return _make_placeholder(scene_description, index, size=(512, 512))


def generate_images_from_script(
    script_text: str,
    image_style: str = "cinematic realistic",
    size: str = "512x512",
) -> List[str]:
    """ينظّف المجلد ويولّد صور لكل المشاهد."""
    # نظّف الإخراج
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
    """واجهة موحّدة يستدعيها بقية المشروع."""
    style = "cinematic realistic, soft contrast, mood lighting, depth of field"
    # 512 أسرع للـ CPU، والمونتاج يرفعها لـ 1080 لاحقًا
    return generate_images_from_script(script_text, image_style=style, size="512x512")


if _name_ == "_main_":
    demo = (
        "مشهد 1: لاعب يربط الحذاء قبل الجري.\n\n"
        "مشهد 2: قطرة عرق تسقط على الأرض.\n\n"
        "مشهد 3: شروق الشمس على المضمار."
    )
    out = generate_images(demo)
    print("✅ Generated images:", out)
