# content_studio/ai_video/video_composer.py

import os
from pathlib import Path
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import logging

# 🗂 المسارات الثابتة للصور، الصوت، والمخرجات
IMAGES_DIR = Path("content_studio/ai_images/outputs/")
AUDIO_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
VIDEO_OUTPUT_DIR = Path("content_studio/ai_video/final_videos/")

def compose_video_from_assets(image_duration: float = 4.0, resolution: tuple = (1080, 1080)) -> str | None:
    """
    🔧 يقوم هذا الملف بدمج الصور المتولدة مع الصوت وتحويلها إلى فيديو نهائي بصيغة MP4.
    
    Args:
        image_duration (float): المدة الزمنية لعرض كل صورة.
        resolution (tuple): أبعاد الفيديو الناتج (عرض، ارتفاع).

    Returns:
        str | None: مسار الفيديو الناتج، أو None في حال وجود خطأ.
    """
    logging.debug("🎬 بدأ تركيب الفيديو من الصور والصوت")

    try:
        # 1️⃣ التحقق من وجود صور
        image_files = sorted(IMAGES_DIR.glob("*.png"))
        if not image_files:
            raise FileNotFoundError("❌ لم يتم العثور على صور داخل المجلد: ai_images/outputs/")

        # 2️⃣ تجهيز مقاطع الفيديو من الصور
        clips = []
        for image_file in image_files:
            clip = ImageClip(str(image_file)).set_duration(image_duration)
            clip = clip.resize(height=resolution[1])
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # 3️⃣ دمج الصوت (إن وُجد)
        if AUDIO_PATH.exists():
            audio = AudioFileClip(str(AUDIO_PATH))
            video = video.set_audio(audio)
            logging.debug("🔊 تم دمج الصوت مع الفيديو")
        else:
            logging.warning("⚠ لم يتم العثور على ملف الصوت، سيتم توليد الفيديو بدون صوت")

        # 4️⃣ إنشاء اسم ومسار الفيديو الناتج
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = VIDEO_OUTPUT_DIR / f"final_video_{timestamp}.mp4"

        # 5️⃣ حفظ الفيديو بصيغة عالية الجودة
        video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="medium",
            bitrate="2000k"
        )

        # 6️⃣ التحقق من وجود الملف النهائي
        if not output_path.exists():
            raise FileNotFoundError("❌ تم توليد الفيديو لكن لم يتم العثور على الملف الناتج!")

        logging.info(f"✅ تم حفظ الفيديو النهائي في: {output_path}")
        return str(output_path)

    except Exception as e:
        logging.error(f"🔥 خطأ أثناء تركيب الفيديو: {e}")
        return None
