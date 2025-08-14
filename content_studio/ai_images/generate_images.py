# content_studio/ai_images/generate_images.py
# -- coding: utf-8 --
from __future__ import annotations

import io
import time
import logging
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("core_engine")
log.setLevel(logging.INFO)

# مجلد الإخراج
IMAGES_DIR = Path("content_studio/ai_images/outputs")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ========= أدوات مساعدة =========
def _extract_scenes(script: str) -> List[str]:
    """يقسم السكربت إلى مشاهد قصيرة."""
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
                     script, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        # لو ما انقسم، خذه فِقرات
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    return scenes[:6] if scenes else [script.strip()[:140]]

def _query_hint(txt: str) -> str:
    """يستخلص كلمات مفتاحية بسيطة للبحث الصوري."""
    txt = txt.lower()
    # مفاتيح رياضية بسيطة
    mapping = [
        ("run", "running"),
        ("jog", "running"),
        ("shoe", "running shoes"),
        ("track", "running track"),
        ("swim", "swimming"),
        ("cycle", "cycling"),
        ("bike", "cycling"),
        ("gym", "gym workout"),
        ("sunrise", "sunrise"),
        ("morning", "morning fitness"),
        ("smile", "smile portrait"),
        ("focus", "athlete focus"),
        ("strength", "strength training"),
        ("football", "football training"),
        ("soccer", "soccer training"),
        ("basketball", "basketball practice"),
        ("tennis", "tennis practice"),
    ]
    for k, v in mapping:
        if k in txt:
            return v
    # افتراضي
    words = re.findall(r"[a-zA-Z]+", txt)
    return " ".join(words[:3]) or "fitness training"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (StockFetcher/1.0; +https://example.org)"
}

def _http_get(url: str, timeout: int = 15, retries: int = 3) -> Optional[bytes]:
    """تحميل مع ريترَي وتباطؤ بسيط."""
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
            if r.ok and r.content:
                return r.content
            log.warning(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            log.warning(f"GET failed ({i+1}/{retries}) {url} -> {e}")
        time.sleep(1.5 * (i + 1))
    return None

def _save_image_bytes(raw: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(raw)

def _placeholder_with_text(text: str, path: Path, size=(1024,1024)) -> None:
    img = Image.new("RGB", size, (22, 24, 28))
    d = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("DejaVuSans.ttf", 64)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 38)
    except Exception:
        font_big = ImageFont.load_default()
        font_body = ImageFont.load_default()

    d.text((40, 40), "Placeholder", fill=(245,245,245), font=font_big)
    y = 140
    # لفّ النص
    words = text.split()
    line = ""
    lines = []
    for w in words:
        if len((line + " " + w).strip()) <= 28:
            line = (line + " " + w).strip()
        else:
            lines.append(line); line = w
    if line: lines.append(line)
    for ln in lines[:10]:
        d.text((40, y), ln, fill=(220,220,220), font=font_body); y += 48
    img.save(path, "PNG")

# ========= جلب صور مجانية بدون مفاتيح =========
def _download_stock(query: str) -> Optional[bytes]:
    """
    يحاول مصادر مجانية بالترتيب:
      1) LoremFlickr (يُرجع صور من فليكر بحسب الكلمة)
      2) Unsplash Source (غير مضمون دائمًا؛ نخليه كاحتياط ثالث)
      3) Picsum (عشوائي بالـ seed، بدون بحث)
    """
    q = quote(query)

    # 1) LoremFlickr (الأفضل للبحث المجاني)
    urls = [
        f"https://loremflickr.com/1024/1024/{q}",
        # 2) Unsplash Source (قد يُرجع 503 أحيانًا)
        f"https://source.unsplash.com/1024x1024/?{q}",
        # 3) Picsum (بدون بحث، لكن صورة فوتو حقيقية)
        f"https://picsum.photos/seed/{q}/1024"
    ]

    for url in urls:
        raw = _http_get(url)
        if raw:
            return raw
    return None

# ========= الدالة الرئيسية التي يستدعيها النظام =========
def generate_images(
    script: str,
    lang: str = "en",
    use_ai_images: bool = False,   # متجاهَلة هنا (لا نستخدم OpenAI)
    use_stock: bool = True,        # لو False سنولّد placeholders فقط
    **kwargs,
) -> List[str]:
    """
    تُرجِع مسارات الصور المتولّدة.
    - عند use_stock=True نحاول جلب صور فوتوغرافية مجانية.
    - لو فشل/رجع 503: نولّد Placeholder محلي.
    """
    # نظّف المجلد
    for f in IMAGES_DIR.glob("*"):
        try: f.unlink()
        except: pass

    scenes = _extract_scenes(script)
    out_paths: List[str] = []

    for i, scene in enumerate(scenes, start=1):
        path = IMAGES_DIR / f"scene_{i}.png"
        query = _query_hint(scene)

        if use_stock:
            raw = _download_stock(query)
            if raw:
                try:
                    # نتأكد أنها صورة صالحة
                    Image.open(io.BytesIO(raw)).convert("RGB").save(path, "PNG")
                    log.info(f"STOCK ok -> {path}")
                    out_paths.append(str(path)); continue
                except Exception as e:
                    log.warning(f"Validate image failed -> {e}")

        # فولباك: Placeholder
        _placeholder_with_text(scene, path)
        log.warning(f"FALLBACK -> placeholder saved: {path}")
        out_paths.append(str(path))

    return out_paths
