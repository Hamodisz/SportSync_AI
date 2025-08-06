from pathlib import Path
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ✅ عدّل المسارات لتكون متوافقة مع وضعك الحالي
IMAGES_DIR = Path("generated_images/")  # ← هذا مهم!
AUDIO_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
VIDEO_OUTPUT_DIR = Path("content_studio/ai_video/final_videos/")
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def compose_video_from_assets(image_duration=4.0, resolution=(1080, 1080)) -> str | None:
    try:
        # التأكد من وجود صور
        image_files = sorted([f for f in IMAGES_DIR.glob("*.png")])
        if not image_files:
            raise Exception(f"❌ لا توجد صور داخل المجلد: {IMAGES_DIR}")

        # تجهيز مقاطع الفيديو من الصور
        clips = []
        for image_file in image_files:
            clip = ImageClip(str(image_file)).set_duration(image_duration)
            clip = clip.resize(height=resolution[1])
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # دمج الصوت
        audio = AudioFileClip(str(AUDIO_PATH))
        video = video.set_audio(audio)

        # حفظ الفيديو النهائي
        output_path = VIDEO_OUTPUT_DIR / f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        video.write_videofile(str(output_path), fps=24)

        return str(output_path)

    except Exception as e:
        print("❌ فشل التوليد:", e)
        return None
