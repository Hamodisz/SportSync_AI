# content_studio/ai_images/generate_images.py
# توليد صور: يجرّب OpenAI (اختياري) -> صور ستوك مجانية -> Placeholder محلي

import os, io, textwrap, random, time
from pathlib import Path
from typing import List
import requests
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path("content_studio/ai_images/outputs"); OUT_DIR.mkdir(parents=True, exist_ok=True)

def _placeholder(text: str, idx: int, size=(1024,1024)) -> Path:
    img = Image.new("RGB", size, (20,24,28))
    d = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("DejaVuSans.ttf", 64)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 40)
    except:
        font_big = ImageFont.load_default(); font_body = ImageFont.load_default()
    d.text((40,40), f"Scene {idx+1}", fill=(245,245,245), font=font_big)
    y = 140
    for ln in textwrap.wrap(text, width=28)[:10]:
        d.text((40,y), ln, fill=(220,220,220), font=font_body); y += 52
    out = OUT_DIR / f"scene_{idx+1}.png"; img.save(out, "PNG"); return out

def _split_scenes(script: str) -> List[str]:
    parts = [p.strip() for p in script.replace("\r","").split("\n") if p.strip()]
    # خذ الأسطر التي تبدو كوصف مشهد
    scenes = []
    buf = []
    for line in parts:
        if line.lower().startswith(("scene","مشهد","outro","title")) and buf:
            scenes.append(" ".join(str(x) for x in buf)); buf=[line]
        else:
            buf.append(line)
    if buf: scenes.append(" ".join(str(x) for x in buf))
    return scenes[:4] if scenes else [script.strip()[:140]]

def _try_openai(prompt: str) -> bytes | None:
    if os.getenv("USE_OPENAI","0") != "1": return None
    key = os.getenv("OPENAI_API_KEY"); 
    if not key: return None
    try:
        # Images API (DALL·E-style)
        r = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {key}"},
            json={"model":"gpt-image-1","prompt": prompt,"size":"1024x1024"},
            timeout=60,
        )
        if r.status_code != 200: return None
        b64 = r.json()["data"][0]["b64_json"]
        return io.BytesIO(base64.b64decode(b64)).getvalue()
    except Exception:
        return None

STOCK_SOURCES = [
    "https://picsum.photos/seed/{seed}/1024",
    "https://loremflickr.com/1024/1024/{query}",
    "https://source.unsplash.com/1024x1024/?{query}",
]

def _try_stock(query: str) -> bytes | None:
    for url in STOCK_SOURCES:
        u = url.format(query=query, seed=random.randint(1,999999))
        try:
            r = requests.get(u, timeout=25)
            if r.status_code == 200 and r.content:
                return r.content
        except Exception:
            pass
    return None

def generate_images(script: str, lang: str, use_stock: bool = True, use_openai: bool = False) -> List[str]:
    # تنظيف قديم
    for f in OUT_DIR.glob("*"):
        try: f.unlink()
        except Exception: pass

    scenes = _split_scenes(script) or ["Start…", "Keep moving…", "Results…", "Outro…"]
    outs: List[str] = []

    for i, sc in enumerate(scenes):
        img_bytes = None
        if use_openai:
            img_bytes = _try_openai(sc)
        if img_bytes is None and use_stock:
            q = "running track" if "run" in sc.lower() else "sport fitness"
            img_bytes = _try_stock(q)

        if img_bytes:
            try:
                out = OUT_DIR / f"scene_{i+1}.png"
                Image.open(io.BytesIO(img_bytes)).convert("RGB").save(out, "PNG")
                outs.append(str(out)); continue
            except Exception:
                pass

        # Placeholder كحل أخير
        out = _placeholder(sc, i); outs.append(str(out))
        time.sleep(0.05)

    return outs
