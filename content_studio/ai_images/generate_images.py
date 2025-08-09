# content_studio/ai_images/generate_images.py
# -- coding: utf-8 --

from _future_ import annotations

import os
import re
import time
import base64
import logging
from pathlib import Path
from typing import List, Optional

# ========= Logging =========
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | ai_images | %(message)s"
)

# ========= Paths =========
OUTPUT_DIR = Path("content_studio/ai_images/outputs/")
SAMPLE_DIR = Path("generated_images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ========= Optional deps / OpenAI client =========
USE_OPENAI = False
client = None

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:
    from openai import OpenAI  # type: ignore
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
        USE_OPENAI = True
        logging.info("OpenAI client configured.")
    else:
        logging.warning("OPENAI_API_KEY not set. Falling back to local generation.")
except Exception as e:
    logging.warning(f"OpenAI client not available, will use fallbacks. ({e})")
    USE_OPENAI = False
    client = None

# Local fallback
from PIL import Image, ImageDraw, ImageFont  # type: ignore


# ========= Helpers =========
def extract_scenes(script_text: str) -> List[str]:
    """
    Extract scenes from Arabic/English script.
    Supports:
      - Scene #1: ...
      - مشهد 1: ...
    Falls back to splitting on empty lines.
    """
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
                     script_text, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script_text) if p.strip()]

    # Cap at 6 scenes for short videos
    return scenes[:6] if scenes else [script_text.strip()[:140]]


def _save_png_from_b64(b64_data: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(b64_data))


def _copy_from_samples(idx: int) -> Optional[str]:
    """
    Quick fallback: copy one of ./generated_images/.png|.jpg into outputs.
    """
    if not SAMPLE_DIR.exists():
        return None
    candidates = sorted(list(SAMPLE_DIR.glob(".png")) + list(SAMPLE_DIR.glob(".jpg")))
    if not candidates:
        return None

    src = candidates[idx % len(candidates)]
    dst = OUTPUT_DIR / f"scene_{idx + 1}{src.suffix.lower()}"
    Image.open(src).save(dst)  # ensure valid format
    return str(dst)


def _make_text_image(text: str, idx: int, size=(1024, 1024)) -> str:
    """
    Final offline fallback: render the scene text onto a simple poster image.
    """
    img = Image.new("RGB", size, (18, 20, 24))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 44)
    except Exception:
        font = ImageFont.load_default()

    # naive wrap
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len((line + " " + w).strip()) < 28:
            line = (line + " " + w).strip()
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)

    y = 80
    for ln in lines[:12]:
        draw.text((60, y), ln, fill=(235, 235, 235), font=font)
        y += 60

    path = OUTPUT_DIR / f"scene_{idx + 1}.png"
    img.save(path, format="PNG")
    return str(path)


def _generate_openai_image(prompt: str, idx: int, size: str, retries: int = 3) -> str:
    """
    Generate an image via OpenAI Images API (gpt-image-1) with retries.
    Raises on final failure so fallbacks trigger.
    """
    if not USE_OPENAI or client is None:
        raise RuntimeError("OpenAI not configured")

    style_suffix = "\nStyle: cinematic, realistic, dramatic lighting, high detail."
    full_prompt = (prompt or "").strip() + style_suffix

    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = client.images.generate(
                model="gpt-image-1",
                prompt=full_prompt,
                size=size,
                # NOTE: allowed values (low|medium|high|auto). 'standard' causes 400.
                quality="high",
                n=1,
            )
            b64_img = resp.data[0].b64_json
            out_path = OUTPUT_DIR / f"scene_{idx + 1}.png"
            _save_png_from_b64(b64_img, out_path)
            return str(out_path)
        except Exception as e:
            last_err = e
            wait = 1.5 * attempt
            logging.warning(f"[OpenAI] attempt {attempt} failed ({e}), retrying in {wait:.1f}s…")
            time.sleep(wait)

    raise RuntimeError(f"OpenAI image generation failed after {retries} attempts: {last_err}")


# ========= Public API =========
def generate_image_for_scene(
    scene_description: str,
    index: int,
    image_style: str = "cinematic realistic, dramatic lighting, high detail",
    size: str = "1024x1024",
) -> str:
    """
    Generate one scene image with robust fallbacks:
    OpenAI → sample images → local text poster.
    """
    scene_prompt = f"{scene_description}. Style: {image_style}."
    try:
        if USE_OPENAI:
            return _generate_openai_image(scene_prompt, idx=index, size=size)
        raise RuntimeError("OpenAI disabled or missing")
    except Exception as e:
        logging.info(f"[Fallback] OpenAI unavailable: {e}")
        from_samples = _copy_from_samples(index)
        if from_samples:
            return from_samples
        return _make_text_image(scene_description, index)


def generate_images_from_script(
    script_text: str,
    image_style: str = "cinematic realistic",
    size: str = "1024x1024",
) -> List[str]:
    """
    Turn a script into a list of scene images.
    Cleans output folder first to ensure fresh results.
    """
    for f in OUTPUT_DIR.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

    scenes = extract_scenes(script_text)
    paths: List[str] = []

    for i, scene in enumerate(scenes):
        logging.info(f"🎨 Generating image for scene #{i + 1}…")
        p = generate_image_for_scene(
            scene_description=scene,
            index=i,
            image_style=image_style,
            size=size,
        )
        paths.append(p)
        # tiny delay to avoid hammering APIs/filesystem
        time.sleep(0.05)

    return paths


def generate_images(script_text: str, lang: str = "ar") -> List[str]:
    """
    Entry-point used by the rest of the project.
    """
    style = "cinematic realistic, soft contrast, mood lighting, depth of field"
    return generate_images_from_script(script_text, image_style=style, size="1024x1024")


# ========= Quick self-test =========
if _name_ == "_main_":
    try:
        test_script = (
            "مشهد 1: لاعب يربط الحذاء قبل الجري.\n\n"
            "مشهد 2: قطرة عرق تسقط على الأرض.\n\n"
            "مشهد 3: شروق الشمس على المضمار."
        )
        out = generate_images(test_script)
        print("✅ Generated images:", out)
    except Exception as e:
        logging.error(f"Test run failed: {e}")
