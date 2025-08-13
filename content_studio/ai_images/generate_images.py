# -- coding: utf-8 --
"""
content_studio/ai_images/generate_images.py

توليد صور للمشاهد عبر Pexels API (مجاني) + فولباك Placeholder محلي.
الدالة القياسية التي يستدعيها المشروع: generate_images(script_text, lang="ar")
"""

from _future_ import annotations

import os
import re
import io
import json
import time
import logging
from pathlib import Path
from typing import List, Optional

import requests
from PIL import Image, ImageDraw, ImageFont

# ===== لوجينغ =====
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | ai_images | %(message)s",
)

# ===== مسارات =====
OUTPUT_DIR = Path("content_studio/ai_images/outputs/")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ===== إعدادات Pexels =====
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
USE_PEXELS = bool(PEXELS_API_KEY)

# بناء رابط بسيط للإسناد (مطلوب ضمن إرشادات Pexels) — للتوثيق فقط
ATTR_LOG = OUTPUT_DIR / "_attribution.json"

# ===== أدوات مساعدة =====
def extract_scenes(script_text: str) -> List[str]:
    """
    يقسم السكربت إلى مشاهد. يقبل:
      - Scene #1: ... / Scene: ...
      - مشهد 1: ... / مشهد: ...
      - وإلا يقسم على الأسطر الفارغة.
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

def _wrap_lines(text: str, max_len: int = 28) -> List[str]:
    words = text.split()
    out, line = [], ""
    for w in words:
        nxt = (line + " " + w).strip()
        if len(nxt) <= max_len:
            line = nxt
        else:
            if line: out.append(line)
            line = w
    if line: out.append(line)
    return out

def _center_crop_to_square(img: Image.Image, size: int = 1080) -> Image.Image:
    """قص مركزي لمربع ثم تغيير الحجم."""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    return img.resize((size, size), Image.LANCZOS)

def _draw_placeholder(text: str, idx: int, size: int = 1080) -> str:
    """إنشاء صورة نصّية محليًا (Fallback)"""
    img = Image.new("RGB", (size, size), (20, 24, 28))
    d = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("arial.ttf", 64)
        font_body  = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font_title = ImageFont.load_default()
        font_body  = ImageFont.load_default()

    d.text((40, 40), f"Scene {idx+1}", fill=(245, 245, 245), font=font_title)
    y = 140
    for ln in _wrap_lines(text, 30)[:12]:
        d.text((40, y), ln, fill=(220, 220, 220), font=font_body)
        y += 52

    out = OUTPUT_DIR / f"scene_{idx+1}.png"
    img.save(out, "PNG")
    return str(out)

# ===== Pexels =====
def _pexels_search_image(query: str) -> Optional[dict]:
    """
    يبحث عن صورة واحدة مناسبة في Pexels ويرجع كائن الصورة (أو None).
    نستخدم orientation=square ليتماشى مع الفيديو المربّع.
    """
    if not USE_PEXELS:
        return None
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": 1,
        "orientation": "square",
        # ممكن تضيف "size": "large" لو تحتاج دقة أعلى
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            logging.warning(f"[Pexels] HTTP {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()
        photos = data.get("photos", [])
        if not photos:
            return None
        return photos[0]
    except Exception as e:
        logging.warning(f"[Pexels] request failed: {e}")
        return None

def _download_pexels_photo(photo: dict, out_path: Path) -> bool:
    """يحمل الصورة من Pexels ويحفظها كمربّع 1080x1080."""
    # نختار landscape/original حسب المتاح
    src = photo.get("src") or {}
    cand_urls = [
        src.get("original"),
        src.get("landscape"),
        src.get("large2x"),
        src.get("large"),
        src.get("portrait"),
        src.get("medium"),
    ]
    file_url = next((u for u in cand_urls if u), None)
    if not file_url:
        return False
    try:
        rr = requests.get(file_url, timeout=30)
        rr.raise_for_status()
        img = Image.open(io.BytesIO(rr.content)).convert("RGB")
        img = _center_crop_to_square(img, 1080)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, "PNG")

        # اجمع إسناد بسيط
        credit = {
            "id": photo.get("id"),
            "url": photo.get("url"),
            "photographer": photo.get("photographer"),
            "photographer_url": photo.get("photographer_url"),
            "saved_as": str(out_path.name),
        }
        try:
            old = []
            if ATTR_LOG.exists():
                old = json.loads(ATTR_LOG.read_text(encoding="utf-8"))
            old.append(credit)
            ATTR_LOG.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        return True
    except Exception as e:
        logging.warning(f"[Pexels] download failed: {e}")
        return False

def _keywords_from_scene(text: str) -> str:
    """
    تبسيط نص المشهد إلى كلمات مفتاحية للبحث.
    أمثلة: "شروق هادئ على مضمار" → "sunrise running track calm"
    """
    # بدائي لكن فعّال كبداية
    t = re.sub(r"[^\w\s\u0600-\u06FF]+", " ", text)  # احذف الرموز
    t = re.sub(r"\s+", " ", t).strip()
    # لو عربي، ما نلمس كثير — Pexels يدعم Queries عامة
    # اختصر النص لعدد كلمات مناسب
    words = t.split()[:8]
    return " ".join(words) or "motivational sport"

# ===== الواجهة الرئيسية =====
def generate_image_for_scene(scene_description: str, index: int) -> str:
    """
    يولّد صورة واحدة لمشهد إما من Pexels أو Placeholder محلي.
    """
    # جرّب Pexels أولاً إن كان المفتاح متاح
    if USE_PEXELS:
        query = _keywords_from_scene(scene_description)
        photo = _pexels_search_image(query)
        if photo:
            out_path = OUTPUT_DIR / f"scene_{index+1}.png"
            if _download_pexels_photo(photo, out_path):
                logging.info(f"[Pexels] scene #{index+1} → {out_path.name} | {photo.get('url')}")
                return str(out_path)

    # فولباك: Placeholder
    logging.info(f"[Fallback] using placeholder for scene #{index+1}")
    return _draw_placeholder(scene_description, index)

def generate_images_from_script(script_text: str) -> List[str]:
    # نظّف الإخراج
    for f in OUTPUT_DIR.glob("*"):
        try: f.unlink()
        except Exception: pass

    scenes = extract_scenes(script_text)
    paths: List[str] = []
    for i, scene in enumerate(scenes):
        p = generate_image_for_scene(scene, i)
        paths.append(p)
        # خفّف الضغط على API المجانية
        time.sleep(0.2)
    return paths

def generate_images(script_text: str, lang: str = "ar") -> List[str]:
    """دالة قياسية يستدعيها core_engine."""
    return generate_images_from_script(script_text)

# اختبار يدوي سريع
if _name_ == "_main_":
    demo = (
        "Scene 1: Sunrise over a running track — Every beginning is a step.\n\n"
        "Scene 2: Laces tightening — Start with one simple move.\n\n"
        "Scene 3: A calm smile — Consistency beats perfection."
    )
    out = generate_images(demo)
    print("✅ Generated images:", out)
