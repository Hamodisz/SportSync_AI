# -- coding: utf-8 --
from __future__ import annotations

import logging
import os
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


from content_studio.ai_images.generate_images import generate_images

try:  # optional imports; engine should still run without them
    from content_studio.ai_voice.voice_generator import (
        generate_voice_from_script,
    )
except Exception:  # pragma: no cover
    generate_voice_from_script = None  # type: ignore

try:
    from content_studio.ai_video.video_composer import (
        compose_video_from_assets,
    )
except Exception:  # pragma: no cover
    compose_video_from_assets = None  # type: ignore

try:
    from content_studio.generate_script.script_generator import generate_script
except Exception:  # pragma: no cover
    generate_script = None  # type: ignore


def _ensure_tools_available() -> List[str]:
    return []


def quick_diagnose() -> Dict:
    return {
        "images_dir_exists": IMAGES_DIR.exists(),
        "images_count": len(list(IMAGES_DIR.glob("*.png")))
        + len(list(IMAGES_DIR.glob("*.jpg"))),
        "voice_exists": VOICE_PATH.exists(),
        "voice_size": VOICE_PATH.stat().st_size if VOICE_PATH.exists() else 0,
        "final_videos_dir_exists": FINAL_VIDS_DIR.exists(),
        "tools_missing": _ensure_tools_available(),
    }


def _fallback_compose_video(
    image_duration: int = 4, fps: int = 30, voice: Optional[str] = None
) -> str:
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

    images = sorted(list(IMAGES_DIR.glob("*.png")) + list(IMAGES_DIR.glob("*.jpg")))
    if not images:
        raise ValueError("لا توجد صور في مجلد الإخراج.")
    clips = [ImageClip(str(p)).set_duration(image_duration) for p in images]
    audio_clip = None
    video = concatenate_videoclips(clips, method="compose")
    if voice and Path(voice).exists():
        audio_clip = AudioFileClip(str(voice))
        video = video.set_audio(audio_clip)
    out = FINAL_VIDS_DIR / "final_video.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    logging.info("🎞️ writing video to %s", out)
    video.write_videofile(
        str(out), fps=fps, codec="libx264", audio_codec="aac", logger=None
    )
    logging.info("✅ video exported: %s", out)
    video.close()
    for c in clips:
        try:
            c.close()
        except Exception:
            pass
    if audio_clip:
        try:
            audio_clip.close()
        except Exception:
            pass
    return str(out.resolve())


def run_full_generation(
    user_data: Dict,
    lang: str = "ar",
    image_duration: int = 4,
    override_script: Optional[str] = None,
    mute_if_no_voice: bool = True,
    skip_cleanup: bool = True,
    use_stock_flag: Optional[bool] = None,
    use_openai_flag: Optional[bool] = None,
) -> Dict:
    try:
        if use_stock_flag is None:
            use_stock_flag = os.getenv("USE_STOCK_IMAGES", "1") == "1"
        if use_openai_flag is None:
            use_openai_flag = os.getenv("USE_OPENAI_IMAGES", "0") == "1"

        if not skip_cleanup and IMAGES_DIR.exists():
            for f in IMAGES_DIR.glob("*"):
                if f.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                    try:
                        f.unlink()
                    except Exception:
                        pass

        # 1) script
        if override_script and override_script.strip():
            script = override_script.strip()
            logging.info("📝 استخدمنا سكربت جاهز (override_script).")
        else:
            if generate_script:
                script = generate_script(
                    topic=user_data.get("topic", "sports motivation"),
                    tone=user_data.get("traits", {}).get("tone", "emotional"),
                    lang="arabic" if lang == "ar" else "english",
                )
            else:
                script = (
                    "Scene 1: Start small.\n\n"
                    "Scene 2: Keep going when no one sees you.\n\n"
                    "Scene 3: Results come to those who don't stop."
                )

        # 2) images
        try:
            images = generate_images(
                script,
                lang=lang,
                use_stock=use_stock_flag,
                use_openai=use_openai_flag,
            )
        except Exception as e:
            logging.warning("تعذّر توليد الصور: %s", e)
            images = [
                str(p)
                for p in sorted(IMAGES_DIR.glob("*.png"))
                + sorted(IMAGES_DIR.glob("*.jpg"))
            ]
        if not images:
            raise RuntimeError("لم يتم توليد أي صور.")

        # 3) voice (optional)
        voice_path = None
        if generate_voice_from_script:
            try:
                voice_path = generate_voice_from_script(script, lang)
            except Exception as e:
                logging.warning("تعذّر توليد الصوت: %s", e)
                if not mute_if_no_voice:
                    raise

        # 4) video
        if compose_video_from_assets:
            logging.info("🎬 composing video …")
            try:
                video_path = compose_video_from_assets(
                    image_duration=image_duration, voice_path=voice_path
                )
            except TypeError:
                video_path = compose_video_from_assets(image_duration=image_duration)
        else:
            video_path = _fallback_compose_video(
                image_duration=image_duration, voice=voice_path
            )

        return {
            "script": str(script),
            "images": images,
            "voice": voice_path,
            "video": str(Path(video_path).resolve()) if video_path else None,
            "error": None,
        }
    except Exception as e:  # pragma: no cover - runtime safety
        logging.error("🔥 فشل التشغيل: %s", e)
        return {
            "script": None,
            "images": [],
            "voice": None,
            "video": None,
            "error": str(e),
        }


__all__ = ["run_full_generation", "quick_diagnose"]

