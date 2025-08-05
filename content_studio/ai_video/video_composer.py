import os
from pathlib import Path
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
AUDIO_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
VIDEO_OUTPUT_DIR = Path("content_studio/ai_video/final_videos/")

def compose_video_from_assets(image_duration=4.0, resolution=(1080, 1080)) -> str | None:
    try:
        # 1. التحقق من وجود الصور
        image_files = sorted([f for f in IMAGES_DIR.glob("*.png")])
        if not image_files:
            raise Exception("❌ لا توجد صور داخل ai_images/outputs/")

        # 2. تجهيز المقاطع من الصور
        clips = []
        for image_file in image_files:
            clip = ImageClip(str(image_file)).set_duration(image_duration)
            clip = clip.resize(height=resolution[1])
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # 3. دمج الصوت (اختياري)
        if AUDIO_PATH.exists():
            audio = AudioFileClip(str(AUDIO_PATH))
            video = video.set_audio(audio)

        # 4. تحديد اسم الفيديو النهائي (بـ timestamp)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = VIDEO_OUTPUT_DIR / f"final_video_{timestamp}.mp4"

        # 5. حفظ الفيديو
        video.write_videofile(str(output_path), fps=24)

        # 6. تأكيد أن الملف تولد فعلاً
        if not output_path.exists():
            raise Exception("⚠ تم حفظ الفيديو لكن لم يتم العثور على الملف الناتج!")

        return str(output_path)

    except Exception as e:
        print(f"🔥 خطأ أثناء تركيب الفيديو: {e}")
        return None
