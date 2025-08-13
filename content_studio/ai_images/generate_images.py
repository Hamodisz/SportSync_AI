# -- coding: utf-8 --
from _future_ import annotations

import re
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def _wrap_lines(text: str, max_len: int = 30) -> List[str]:
    words = text.split()
    out, line = [], ""
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

def _extract_scenes(script: str, limit: int = 12) -> List[str]:
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

def _make_placeholder(text: str, idx: int, size: tuple[int, int] = (1080, 1080)) -> Path:
    img = Image.new("RGB", size, (20, 24, 28))
    d = ImageDraw.Draw(img)
    font_big, font_body = _load_fonts()

    d.text((48, 48), f"Scene {idx+1}", fill=(245, 245, 245), font=font_big)
    y = 160
    for ln in _wrap_lines(text, 30)[:12]:
        d.text((48, y), ln, fill=(220, 220, 220), font=font_body)
        y += 52

    out = IMAGES_DIR / f"scene_{idx+1}.png"
    img.save(out, "PNG")
    return out

def generate_images(script: str, lang: str = "ar", seed: Optional[int] = None) -> List[str]:
    # تنظيف قديم
    for f in IMAGES_DIR.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

    scenes = _extract_scenes(script)
    paths = [_make_placeholder(s, i) for i, s in enumerate(scenes)]
    return [str(p) for p in paths]

_all_ = ["generate_images"]
