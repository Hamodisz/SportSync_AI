# -- coding: utf-8 --
from __future__ import annotations

import base64
import logging
import os
import re
import time
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont

try:  # openai is optional at runtime
    from openai import OpenAI
except Exception:  # pragma: no cover - missing dependency
    OpenAI = None  # type: ignore


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | ai_images | %(message)s",
)

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _wrap_lines(text: str, max_len: int = 30) -> List[str]:
    words = text.split()
    out: List[str] = []
    line = ""
    for w in words:
        nxt = (line + " " + w).strip()
        if len(nxt) <= max_len:
            line = nxt
        else:
            if line:
                out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def _extract_scenes(script: str, limit: int = 8) -> List[str]:
    parts = re.split(
        r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
        script,
        flags=re.IGNORECASE,
    )
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    if not scenes:
        scenes = [script.strip()]
    return scenes[:limit]


def _load_fonts() -> tuple[ImageFont.ImageFont, ImageFont.ImageFont]:
    try:
        big = ImageFont.truetype("DejaVuSans.ttf", 64)
        body = ImageFont.truetype("DejaVuSans.ttf", 40)
    except Exception:
        big = ImageFont.load_default()
        body = ImageFont.load_default()
    return big, body


def _placeholder(text: str, idx: int, size: tuple[int, int] = (1024, 1024)) -> Path:
    img = Image.new("RGB", size, (20, 24, 28))
    d = ImageDraw.Draw(img)
    font_big, font_body = _load_fonts()

    d.text((48, 48), f"Scene {idx + 1}", fill=(245, 245, 245), font=font_big)
    y = 160
    for ln in _wrap_lines(text, 30)[:12]:
        d.text((48, y), ln, fill=(220, 220, 220), font=font_body)
        y += 52

    out = IMAGES_DIR / f"scene_{idx + 1}.png"
    img.save(out, "PNG")
    logging.info("🖼️ placeholder saved: %s", out)
    return out


def generate_images(script: str, lang: str = "en", use_ai: bool = True) -> List[str]:
    """Generate images for each scene in *script*.

    Returns list of relative paths to generated PNG files.
    """

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for f in IMAGES_DIR.glob("*.png"):
        try:
            f.unlink()
        except Exception:
            pass

    scenes = _extract_scenes(script)

    api_key = os.getenv("OPENAI_API_KEY")
    use_ai = use_ai and bool(api_key)
    if not use_ai:
        if not api_key:
            logging.warning("OPENAI_API_KEY missing; using placeholders.")
        else:
            logging.info("AI image generation disabled; using placeholders.")

    client = None
    if use_ai and OpenAI:
        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:  # pragma: no cover
            logging.warning("OpenAI client init failed: %s", e)
            client = None
            use_ai = False

    paths: List[Path] = []
    for i, scene in enumerate(scenes):
        out_path = IMAGES_DIR / f"scene_{i + 1}.png"
        if use_ai and client:
            try:
                prompt = scene.strip() or f"Scene {i + 1}"
                resp = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size="1024x1024",
                )
                b64 = resp.data[0].b64_json
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(b64))
                logging.info("🖼️ AI image saved: %s", out_path)
                paths.append(out_path)
                time.sleep(1.0)
                continue
            except Exception as e:
                logging.warning(
                    "AI image failed for scene %s (%s); using placeholder.",
                    i + 1,
                    e,
                )
        # fallback placeholder
        paths.append(_placeholder(scene, i))

    return [str(p) for p in paths]


__all__ = ["generate_images"]

