# core/core_engine.py
from __future__ import annotations

import logging, os
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | core_engine | %(message)s",
)

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
FINAL_VIDS_DIR = Path("content_studio/ai_video/final_videos/")
for p in (IMAGES_DIR, VOICE_PATH.parent, FINAL_VIDS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ↓↓↓ لا يوجد أي import من core.core_engine هنا (حتى لا يحدث circular import)
_generate_script_fn = None
try:
    from content_studio.generate_script.script_generator import generate_script as _generate_script_fn
except Exception:
    pass

_generate_images_fn = None
try:
    from content_studio.ai_images.generate_images import generate_images as _generate_images_fn
except Exception:
    pass

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
    if _generate_images_fn is None:
        missing.append("generate_images")
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
                    topic=user_data.get("topic","sports motivation"),
                    tone=user_data.get("traits",{}).get("tone","emotional"),
                    lang="arabic" if lang=="ar" else "english",
                )
            else:
                script = ("Scene 1: Start.\n\nScene 2: Keep moving.\n\nScene 3: Results follow.")

        # 2) صور
        if _generate_images_fn is None:
            raise RuntimeError("دالة generate_images غير متوفرة.")
        try:
            images = _generate_images_fn(
                script, lang,
                use_stock=os.getenv("USE_STOCK","0")=="1",
                use_openai=os.getenv("USE_OPENAI","0")=="1"
            )
        except TypeError:
            images = _generate_images_fn(script, lang)
        if not images:
            raise RuntimeError("لم يتم توليد أي صور.")

        # 3) صوت (اختياري)
        voice_path = None
        if _generate_voice_fn:
            try:
                try:
                    voice_path = _generate_voice_fn(script, lang)
                except TypeError:
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
            "images": [str(p) for p in sorted(IMAGES_DIR.glob("*"))],
            "voice": str(voice_path) if voice_path else None,
            "video": str(video_path),
            "error": None,
        }

    except Exception as e:
        logging.error(f"🔥 فشل التشغيل: {e}")
        return {"script": None, "images": [], "voice": None, "video": None, "error": str(e)}
