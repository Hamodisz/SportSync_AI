# -- coding: utf-8 --
"""
تركيب الفيديو من الصور (وإضافة صوت اختياري) باستخدام MoviePy.
مهيأ لتقليل ضجيج ffmpeg على Render/Heroku وغيرها.
"""

import os
from pathlib import Path
from typing import Optional

# اخفض ضجيج ffmpeg في اللوق (imageio-ffmpeg)
os.environ["IMAGEIO_FFMPEG_LOGLEVEL"] = "quiet"

IMAGES_DIR      = Path("content_studio/ai_images/outputs/")
FINAL_VIDS_DIR  = Path("content_studio/ai_video/final_videos/")
for p in (IMAGES_DIR, FINAL_VIDS_DIR):
    p.mkdir(parents=True, exist_ok=True)


def compose_video_from_assets(image_duration: int = 4, voice_path: Optional[str] = None, fps: int = 24) -> str:
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

    images = sorted(list(IMAGES_DIR.glob(".png")) + list(IMAGES_DIR.glob(".jpg")))
    if not images:
        raise ValueError("لا توجد صور في مجلد الإخراج.")

    clips = [ImageClip(str(p)).set_duration(image_duration) for p in images]
    video = concatenate_videoclips(clips, method="compose")

    if voice_path and Path(voice_path).exists():
        video = video.set_audio(AudioFileClip(str(voice_path)))

    out = FINAL_VIDS_DIR / "final_video.mp4"
    video.write_videofile(
        str(out),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        logger=None,  # يوقف شريط التقدّم في اللوق
        ffmpeg_params=["-preset", "veryfast", "-movflags", "+faststart"],
    )
    return str(out)
