# content_studio/ai_images/generate_images.py
# توليد صور: RunPod/Flux (أفضل) -> OpenAI (اختياري) -> صور ستوك -> Placeholder

import os, io, textwrap, random, time, base64
from pathlib import Path
from typing import List, Optional
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

def _try_stock(query: str) -> Optional[bytes]:
    for url in STOCK_SOURCES:
        u = url.format(query=query, seed=random.randint(1,999999))
        try:
            r = requests.get(u, timeout=25)
            if r.status_code == 200 and r.content:
                return r.content
        except Exception:
            pass
    return None

def _try_runpod(prompt: str, width: int = 1024, height: int = 1024) -> Optional[bytes]:
    """
    توليد صورة عبر RunPod/Flux

    Args:
        prompt: النص الوصفي
        width: العرض
        height: الارتفاع

    Returns:
        bytes أو None
    """
    # تحقق من التفعيل
    if os.getenv("USE_RUNPOD_IMAGES", "0") != "1":
        return None

    try:
        from core.runpod_flux_client import RunPodFluxClient, enhance_prompt_for_sport

        # إنشاء العميل
        client = RunPodFluxClient()

        # تحسين الـ prompt
        enhanced_prompt = enhance_prompt_for_sport(prompt, lang="en")

        # توليد الصورة
        result = client.generate_image(
            prompt=enhanced_prompt,
            width=width,
            height=height,
            steps=20,  # سريع نسبياً
            cfg_scale=7.5
        )

        if result.get("success"):
            # فك تشفير base64
            img_b64 = result["image_b64"]
            return base64.b64decode(img_b64)
        else:
            print(f"⚠️ RunPod failed: {result.get('error', 'Unknown')}")
            return None

    except Exception as e:
        print(f"⚠️ RunPod exception: {e}")
        return None

def generate_images(
    script: str,
    lang: str,
    use_runpod: bool = True,
    use_stock: bool = True,
    use_openai: bool = False,
    aspect: str = "square"
) -> List[str]:
    """
    توليد صور من سكربت

    الأولوية:
    1. RunPod/Flux (أفضل جودة)
    2. OpenAI DALL-E (إن كان مفعل)
    3. Stock images (مجاني)
    4. Placeholder (محلي)

    Args:
        script: السكربت الكامل
        lang: اللغة
        use_runpod: استخدام RunPod
        use_stock: استخدام صور ستوك
        use_openai: استخدام OpenAI
        aspect: نسبة الأبعاد (square/portrait/landscape)
    """
    # تحديد الأبعاد حسب aspect
    if aspect == "portrait":
        width, height = 1024, 1920
    elif aspect == "landscape":
        width, height = 1920, 1080
    else:  # square
        width, height = 1024, 1024

    # تنظيف قديم
    for f in OUT_DIR.glob("*"):
        try: f.unlink()
        except Exception: pass

    scenes = _split_scenes(script) or ["Start…", "Keep moving…", "Results…", "Outro…"]
    outs: List[str] = []

    print(f"\n🎨 Generating {len(scenes)} images ({width}x{height})...")

    for i, sc in enumerate(scenes):
        print(f"  [{i+1}/{len(scenes)}] {sc[:50]}...")

        img_bytes = None

        # 1) جرّب RunPod أولاً (الأفضل)
        if use_runpod and img_bytes is None:
            img_bytes = _try_runpod(sc, width=width, height=height)
            if img_bytes:
                print(f"    ✅ RunPod")

        # 2) OpenAI (إن كان مفعل)
        if use_openai and img_bytes is None:
            img_bytes = _try_openai(sc)
            if img_bytes:
                print(f"    ✅ OpenAI")

        # 3) Stock images
        if use_stock and img_bytes is None:
            q = "running track" if "run" in sc.lower() else "sport fitness"
            img_bytes = _try_stock(q)
            if img_bytes:
                print(f"    ✅ Stock")

        # حفظ الصورة إن وُجدت
        if img_bytes:
            try:
                out = OUT_DIR / f"scene_{i+1}.png"
                Image.open(io.BytesIO(img_bytes)).convert("RGB").save(out, "PNG")
                outs.append(str(out))
                continue
            except Exception as e:
                print(f"    ⚠️ Save failed: {e}")

        # 4) Placeholder كحل أخير
        print(f"    ⚠️ Using placeholder")
        out = _placeholder(sc, i, size=(width, height))
        outs.append(str(out))
        time.sleep(0.05)

    print(f"✅ Generated {len(outs)} images\n")
    return outs
