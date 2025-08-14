# -- coding: utf-8 --
from __future__ import annotations

import base64
import logging
import os
import re
import time
from pathlib import Path
from typing import List

import requests
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote_plus

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

UA = "SportSync/1.0"


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


def _extract_scenes(script: str, limit: int = 6) -> List[str]:
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


def _make_placeholder(text: str, idx: int, size: tuple[int, int] = (1024, 1024)) -> Path:
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
    return out


def _clean_outputs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for f in IMAGES_DIR.glob("*"):
        if f.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            try:
                f.unlink()
            except Exception:
                pass


def _build_query(text: str) -> str:
    text = re.sub(r"[\"'`.,!?;:]+", " ", text)
    words_en = re.findall(r"[A-Za-z]+", text)
    words = words_en if words_en else text.split()
    return quote_plus(" ".join(words[:5]))


def _download(url: str, out_path: Path, provider: str) -> bool:
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=10)
        if resp.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return True
        logging.info("%s download failed (%s)", provider, resp.status_code)
    except Exception as e:  # pragma: no cover
        logging.info("%s download error: %s", provider, e)
    return False


def generate_images(
    script: str,
    lang: str,
    use_stock: bool = False,
    use_openai: bool = False,
) -> List[str]:
    """Generate images for each scene in *script*."""

    _clean_outputs()
    scenes = _extract_scenes(script)

    api_key = os.getenv("OPENAI_API_KEY")
    use_ai = use_openai and bool(api_key)
    if use_openai and not api_key:
        logging.warning("OPENAI_API_KEY missing; falling back to stock/placeholder.")

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
        provider_used = "placeholder"
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
                provider_used = "openai"
                paths.append(out_path)
                logging.info("scene %s -> %s | %s", i + 1, provider_used, out_path)
                time.sleep(1.0)
                continue
            except Exception as e:
                logging.warning("AI image failed for scene %s (%s)", i + 1, e)

        success = False
        query = _build_query(scene)
        out_path = IMAGES_DIR / f"scene_{i + 1}.jpg"

        if use_stock:
            key = os.getenv("PEXELS_API_KEY")
            if not success and key:
                try:
                    resp = requests.get(
                        "https://api.pexels.com/v1/search",
                        params={"query": query, "per_page": 5, "orientation": "portrait"},
                        headers={"Authorization": key, "User-Agent": UA},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for photo in data.get("photos", []):
                            src = photo.get("src", {})
                            for k in ("large2x", "large", "original"):
                                url = src.get(k)
                                if url and _download(url, out_path, "PEXELS"):
                                    provider_used = "pexels"
                                    success = True
                                    break
                            if success:
                                break
                    else:
                        logging.info("PEXELS failed (%s) for scene %s", resp.status_code, i + 1)
                except Exception as e:
                    logging.info("PEXELS error for scene %s: %s", i + 1, e)

            key = os.getenv("UNSPLASH_ACCESS_KEY")
            if not success and key:
                try:
                    resp = requests.get(
                        "https://api.unsplash.com/search/photos",
                        params={
                            "query": query,
                            "per_page": 5,
                            "orientation": "portrait",
                            "content_filter": "high",
                        },
                        headers={"Authorization": f"Client-ID {key}", "User-Agent": UA},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for photo in data.get("results", []):
                            urls = photo.get("urls", {})
                            for k in ("regular", "full"):
                                url = urls.get(k)
                                if url and _download(url, out_path, "UNSPLASH_API"):
                                    provider_used = "unsplash_api"
                                    success = True
                                    break
                            if success:
                                break
                    else:
                        logging.info(
                            "UNSPLASH_API failed (%s) for scene %s",
                            resp.status_code,
                            i + 1,
                        )
                except Exception as e:
                    logging.info("UNSPLASH_API error for scene %s: %s", i + 1, e)

            key = os.getenv("PIXABAY_API_KEY")
            if not success and key:
                try:
                    resp = requests.get(
                        "https://pixabay.com/api/",
                        params={
                            "key": key,
                            "q": query,
                            "image_type": "photo",
                            "per_page": 5,
                            "orientation": "vertical",
                        },
                        headers={"User-Agent": UA},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for hit in data.get("hits", []):
                            for k in ("largeImageURL", "webformatURL"):
                                url = hit.get(k)
                                if url and _download(url, out_path, "PIXABAY"):
                                    provider_used = "pixabay"
                                    success = True
                                    break
                            if success:
                                break
                    else:
                        logging.info("PIXABAY failed (%s) for scene %s", resp.status_code, i + 1)
                except Exception as e:
                    logging.info("PIXABAY error for scene %s: %s", i + 1, e)

            if not success:
                url = f"https://source.unsplash.com/featured/1024x1024/?{query}"
                if _download(url, out_path, "UNSPLASH_SOURCE"):
                    provider_used = "unsplash_source"
                    success = True
                else:
                    logging.info("UNSPLASH_SOURCE failed for scene %s", i + 1)

        if success:
            paths.append(out_path)
        else:
            out_path = _make_placeholder(scene, i)
            provider_used = "placeholder"
            paths.append(out_path)

        logging.info("scene %s -> %s | %s", i + 1, provider_used, out_path)

    return [str(p) for p in paths]


__all__ = ["generate_images"]
