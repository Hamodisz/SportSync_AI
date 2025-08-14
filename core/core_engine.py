# core/core_engine.py
# -- coding: utf-8 --
from pathlib import Path
from typing import Dict, List, Tuple
import io, re, os, base64, logging, traceback

# فيديو/صور/صوت
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS

# مسارات العمل (ثابتة داخل مشروع Render)
ROOT = Path(".").resolve()
IMAGES_DIR = ROOT / "content_studio" / "ai_images" / "outputs"
VOICE_DIR  = ROOT / "content_studio" / "ai_voice" / "voices"
FINAL_DIR  = ROOT / "content_studio" / "ai_video" / "final_videos"
for p in (IMAGES_DIR, VOICE_DIR, FINAL_DIR):
    p.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(asctime)s | %(name)s | %(message)s")
log = logging.getLogger("core_engine")

# -------- Utilities --------
def _wrap(text: str, max_len: int = 30) -> List[str]:
    words, line, out = text.split(), "", []
    for w in words:
        if len((line + " " + w).strip()) <= max_len:
            line = (line + " " + w).strip()
        else:
            out.append(line); line = w
    if line: out.append(line)
    return out[:12]

def _placeholder(text: str, idx: int, size=(1024,1024)) -> Path:
    img = Image.new("RGB", size, (20,24,28))
    d = ImageDraw.Draw(img)
    try:
        font_big  = ImageFont.truetype("DejaVuSans.ttf", 64)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 40)
    except:
        font_big = ImageFont.load_default(); font_body = ImageFont.load_default()
    d.text((40,40), f"Scene {idx+1}", fill=(245,245,245), font=font_big)
    y = 140
    for ln in _wrap(text, 30):
        d.text((40,y), ln, fill=(220,220,220), font=font_body); y += 52
    out = IMAGES_DIR / f"scene_{idx+1}.png"
    img.save(out, "PNG")
    return out

def _extract_scenes(script: str) -> List[str]:
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)", script, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    return scenes[:6] if scenes else [script.strip()[:140]]

# -------- Public: quick diagnose --------
def quick_diagnose() -> Dict:
    return {
        "images_dir_exists": IMAGES_DIR.exists(),
        "images_count": len(list(IMAGES_DIR.glob("*.png"))),
        "voice_exists": (VOICE_DIR / "final_voice.mp3").exists(),
        "voice_size": (VOICE_DIR / "final_voice.mp3").stat().st_size if (VOICE_DIR / "final_voice.mp3").exists() else 0,
        "final_videos_dir_exists": FINAL_DIR.exists(),
        "tools_missing": [],
    }

# -------- Image generation with guaranteed fallback --------
def generate_images_from_script(script: str) -> List[Path]:
    # امسح المخرجات القديمة
    for f in IMAGES_DIR.glob("scene_*.png"):
        try: f.unlink()
        except: pass

    scenes = _extract_scenes(script)
    out_paths: List[Path] = []

    # 1) حاول مصادر مجانية (قد تفشل على Render المجاني/503) — مُعطلة افتراضًا لتجنب التعليق
    use_stock = False  # غيّرها لاحقًا من الواجهة إذا حبيت
    if use_stock:
        try:
            import requests
            for i, s in enumerate(scenes):
                # صور عامة بدون مفتاح API — قد ترجع 403/503، لذلك نحوط بplaceholder دائمًا
                candidates = [
                    f"https://picsum.photos/seed/scene{i+1}/1024/1024",
                ]
                got = False
                for url in candidates:
                    try:
                        r = requests.get(url, timeout=10)
                        if r.ok:
                            p = IMAGES_DIR / f"scene_{i+1}.png"
                            with open(p, "wb") as f:
                                f.write(r.content)
                            out_paths.append(p); got = True; break
                    except Exception:
                        pass
                if not got:
                    out_paths.append(_placeholder(s, i))
        except Exception as e:
            log.warning("Stock sources failed, using placeholders. %s", e)
            out_paths = [_placeholder(s, i) for i,s in enumerate(scenes)]
    else:
        # 2) توليد محلي مؤكد
        out_paths = [_placeholder(s, i) for i,s in enumerate(scenes)]

    return out_paths

# -------- Voice (optional) --------
def generate_voice(script: str, lang: str = "en") -> Path:
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    out = VOICE_DIR / "final_voice.mp3"
    try:
        txt = re.sub(r"\s+", " ", script).strip()
        if len(txt) > 4000:
            txt = txt[:4000]
        gTTS(txt, lang="ar" if lang.lower().startswith("ar") else "en").save(str(out))
        return out
    except Exception as e:
        log.warning("gTTS failed, continue muted: %s", e)
        if out.exists():
            try: out.unlink()
            except: pass
        return Path("")

# -------- Compose video --------
def compose_video(image_paths: List[Path], voice_path: Path|None, seconds_per_image: int = 4) -> Path:
    if not image_paths:
        raise RuntimeError("لا توجد صور في الإخراج.")
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FINAL_DIR / "final_video.mp4"

    clips = [ImageClip(str(p)).set_duration(max(1, seconds_per_image)) for p in image_paths]
    video = concatenate_videoclips(clips, method="compose")

    try:
        if voice_path and voice_path.exists():
            video = video.set_audio(AudioFileClip(str(voice_path)))
    except Exception as e:
        log.warning("Audio attach failed: %s", e)

    # MoviePy → imageio-ffmpeg
    video.write_videofile(str(out_path), fps=24, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    return out_path

# -------- One-shot pipeline --------
def run_full_generation(user_data: Dict) -> Dict:
    """
    user_data = {
        "script": "...",
        "lang": "en" or "ar",
        "seconds_per_image": 4,
        "add_voice": True/False
    }
    """
    try:
        script = user_data.get("script", "").strip()
        lang   = user_data.get("lang", "en")
        spi    = int(user_data.get("seconds_per_image", 4)) or 4
        add_v  = bool(user_data.get("add_voice", False))

        images = generate_images_from_script(script)
        voice  = generate_voice(script, lang) if add_v else Path("")
        video  = compose_video(images, voice if voice else None, seconds_per_image=spi)

        return {
            "ok": True,
            "images": [str(p) for p in images],
            "voice": str(voice) if voice else None,
            "video": str(video)
        }
    except Exception as e:
        log.error("Pipeline failed: %s\n%s", e, traceback.format_exc())
        return {"ok": False, "error": str(e), "debug": quick_diagnose()}
