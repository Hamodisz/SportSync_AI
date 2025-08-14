# content_studio/ai_images/generate_images.py
# -- coding: utf-8 --
from __future__ import annotations

import io
import os
import re
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = Path("content_studio/ai_images/outputs")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "SportSync/1.0 (+https://example.org)"}


def _download_openai(prompt: str) -> Optional[bytes]:
    """Generate an image using OpenAI and return the raw bytes."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.images.generate(prompt=prompt, size="1024x1024")
        url = resp.data[0].url  # type: ignore[index]
        return _http_get(url)
    except Exception as e:  # pragma: no cover - network/API failures
        logging.warning("OpenAI image fetch failed: %s", e)
        return None

# -------- helpers --------
def _extract_scenes(text: str) -> List[str]:
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
                     text, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return scenes[:6] if scenes else [text.strip()[:140]]

def _seed_from_text(s: str) -> str:
    # seed ثابت من نص المشهد (لتكرار نفس الصورة للمشهد نفسه)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

def _http_get(url: str, timeout: int = 10, retries: int = 3) -> Optional[bytes]:
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
            if r.status_code in (403, 503):
                logging.warning("HTTP %s while fetching %s", r.status_code, url)
            if r.ok and r.content:
                return r.content
        except Exception as e:
            logging.warning("HTTP error fetching %s: %s", url, e)
        time.sleep(1.2 * (i + 1))
    return None

def _placeholder(path: Path, text: str, size=(1024, 1024)) -> None:
    img = Image.new("RGB", size, (22,24,28))
    d = ImageDraw.Draw(img)
    try:
        title = ImageFont.truetype("DejaVuSans.ttf", 64)
        body  = ImageFont.truetype("DejaVuSans.ttf", 38)
    except Exception:
        title = ImageFont.load_default()
        body  = ImageFont.load_default()
    d.text((40,40), "Placeholder", fill=(245,245,245), font=title)
    y=140
    line=""; lines=[]
    for w in text.split():
        if len((line+" "+w).strip())<=28: line=(line+" "+w).strip()
        else: lines.append(line); line=w
    if line: lines.append(line)
    for ln in lines[:10]:
        d.text((40,y), ln, fill=(220,220,220), font=body); y+=48
    img.save(path, "PNG")

# -------- single free source (Picsum) --------
def _download_picsum(seed: str) -> Optional[bytes]:
    # صور حقيقية عشوائية بدون API
    url = f"https://picsum.photos/seed/{quote(seed)}/1024"
    return _http_get(url)

# -------- main --------
def generate_images(
    script: str,
    lang: str = "en",
    use_ai_images: bool = False,
    use_stock: bool = True,
    **kwargs,
) -> List[str]:
    # نظّف الإخراج
    for f in IMAGES_DIR.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

    scenes = _extract_scenes(script)
    out: List[str] = []

    for i, scene in enumerate(scenes, start=1):
        path = IMAGES_DIR / f"scene_{i}.png"
        raw: Optional[bytes] = None

        if use_ai_images:
            raw = _download_openai(scene)
            if raw:
                try:
                    Image.open(io.BytesIO(raw)).convert("RGB").save(path, "PNG")
                    out.append(str(path))
                    continue
                except Exception as e:
                    logging.warning("Failed saving OpenAI image: %s", e)

        if use_stock:
            raw = _download_picsum(_seed_from_text(scene))
            if raw:
                try:
                    Image.open(io.BytesIO(raw)).convert("RGB").save(path, "PNG")
                    out.append(str(path))
                    continue
                except Exception as e:
                    logging.warning("Failed saving stock image: %s", e)

        logging.warning("Falling back to placeholder for scene %s", i)
        _placeholder(path, scene)
        out.append(str(path))

    return out
