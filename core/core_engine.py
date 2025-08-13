# -- coding: utf-8 --
from _future_ import annotations

import logging, re
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO,
    format="%(levelname)s | %(asctime)s | core_engine | %(message)s")

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
FINAL_VIDS_DIR = Path("content_studio/ai_video/final_videos/")
for p in (IMAGES_DIR, VOICE_PATH.parent, FINAL_VIDS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ---------- فولباك لتوليد الصور محليًا ----------
from PIL import Image, ImageDraw, ImageFont

def _wrap_lines(text: str, max_len: int = 30) -> List[str]:
    words = text.split()
    out, line = [], ""
    for w in words:
        nxt = (line + " " + w).strip()
        if len(nxt) <= max_len: line = nxt
        else:
            if line: out.append(line)
            line = w
    if line: out.append(line)
    return out

def _extract_scenes(script: str, limit: int = 12) -> List[str]:
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
                     script, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    if not scenes:
        scenes = [script.strip()]
    return scenes[:limit]

def _make_placeholder(text: str, idx: int, size=(1080,1080)) -> Path:
    img = Image.new("RGB", size, (20,24,28))
    d = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("DejaVuSans.ttf", 64)
        body = ImageFont.truetype("DejaVuSans.ttf", 40)
    except Exception:
        big = ImageFont.load_default(); body = ImageFont.load_default()
    d.text((48,48), f"Scene {idx+1}", fill=(245,245,245), font=big)
    y = 160
    for ln in _wrap_lines(text, 30)[:12]:
        d.text((48,y), ln, fill=(220,220,220), font=body); y += 52
    out = IMAGES_DIR / f"scene_{idx+1}.png"
    img.save(out, "PNG")
    return out

def _generate_images_local(script: str, lang: str="ar") -> List[str]:
    for f in IMAGES_DIR.glob("*"):
        try: f.unlink()
        except Exception: pass
    scenes = _extract_scenes(script)
    return [str(_make_placeholder(s, i)) for i, s in enumerate(scenes)]

# --------- استيرادات مرنة ----------
_generate_script_fn = None
try:
    from content_studio.generate_script.script_generator import generate_script as _generate_script_fn
except Exception:
    pass

# سنحاول الاستيراد، وإن فشل نستخدم الفولباك المحلي
def _pick_generate_images():
    try:
        from content_studio.ai_images.generate_images import generate_images as _gen
        return _gen
    except Exception as e:
        logging.warning("⚠ using local image generator fallback (import failed): %s", e)
        return _generate_images_local

_generate_images_fn = _pick_generate_images()

_generate_voice_fn = None
try:
    from content_studio.ai_voice.voice_generator import generate_voice_from_script as _generate_voice_fn
except Exception:
    pass

_compose_video_fn = None
try:
    from content_studio.ai_video.video_composer import compose_video_from_assets as _compose_video_fn
except Exception:
    pass

def _fallback_compose_video(image_duration: int = 4, fps: int = 30, voice: Optional[str] = None) -> str:
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
    images = sorted(list(IMAGES_DIR.glob(".png")) + list(IMAGES_DIR.glob(".jpg")))
    if not images:
        raise ValueError("لا توجد صور في مجلد الإخراج.")
    clips = [ImageClip(str(p)).set_duration(image_duration) for p in images]
    video = concatenate_videoclips(clips, method="compose")
    if voice and Path(voice).exists():
        video = video.set_audio(AudioFileClip(str(voice)))
    out = FINAL_VIDS_DIR / "final_video.mp4"
    video.write_videofile(str(out), fps=fps, codec="libx264", audio_codec="aac")
    return str(out)

def _ensure_tools_available() -> List[str]:
    missing: List[str] = []
    # عندنا فولباك للصور، إذًا ما نعدّها مفقودة
    return missing

def quick_diagnose() -> Dict:
    return {
        "images_dir_exists": IMAGES_DIR.exists(),
        "images_count": len(list(IMAGES_DIR.glob(".png"))) + len(list(IMAGES_DIR.glob(".jpg"))),
        "voice_exists": VOICE_PATH.exists(),
        "voice_size": VOICE_PATH.stat().st_size if VOICE_PATH.exists() else 0,
        "final_videos_dir_exists": FINAL_VIDS_DIR.exists(),
        "tools_missing": _ensure_tools_available(),
    }

def run_full_generation(
    user_data: Dict,
    lang: str = "ar",
    image_duration: int = 4,
    override_script: Optional[str] = None,
    mute_if_no_voice: bool = True,
    skip_cleanup: bool = True,
) -> Dict:
    try:
        if not skip_cleanup and IMAGES_DIR.exists():
            for f in IMAGES_DIR.glob("*"):
                try: f.unlink()
                except Exception: pass

        # 1) سكربت
        if override_script and override_script.strip():
            script = override_script.strip()
            logging.info("📝 استخدمنا سكربت جاهز (override_script).")
        else:
            if _generate_script_fn:
                script = _generate_script_fn(
                    topic=user_data.get("topic", "sports motivation"),
                    tone=user_data.get("traits", {}).get("tone", "emotional"),
                    lang="arabic" if lang == "ar" else "english",
                )
            else:
                script = (
                    "Scene 1: Start small.\n\n"
                    "Scene 2: Keep going when no one sees you.\n\n"
                    "Scene 3: Results come to those who don’t stop."
                )

        # 2) صور
        images = _generate_images_fn(script, lang)
        if not images:
            raise RuntimeError("لم يتم توليد أي صور.")

        # 3) صوت (اختياري)
        voice_path = None
        if _generate_voice_fn:
            try:
                # بعض الإصدارات تختلف توقيعها
                if getattr(generate_voice_fn, "code", None) and _generate_voice_fn.code_.co_argcount >= 2:
                    voice_path = _generate_voice_fn(script, lang)
                else:
                    voice_path = _generate_voice_fn(script)
            except Exception as e:
                logging.warning(f"تعذّر توليد الصوت: {e}")
                if not mute_if_no_voice:
                    raise

        # 4) فيديو
        if _compose_video_fn:
            try:
                video_path = _compose_video_fn(image_duration=image_duration, voice_path=voice_path)
            except TypeError:
                video_path = _compose_video_fn(image_duration=image_duration)
        else:
            video_path = _fallback_compose_video(image_duration=image_duration, voice=voice_path)

        return {
            "script": str(script),
            "images": [str(p) for p in IMAGES_DIR.glob("*")],
            "voice": str(voice_path) if voice_path else None,
            "video": str(video_path),
            "error": None,
        }
    except Exception as e:
        logging.error(f"🔥 فشل التشغيل: {e}")
        return {"script": None, "images": [], "voice": None, "video": None, "error": str(e)}
