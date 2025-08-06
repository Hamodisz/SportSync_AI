import os
from pathlib import Path
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
AUDIO_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
VIDEO_OUTPUT_DIR = Path("content_studio/ai_video/final_videos/")

def compose_video_from_assets(image_duration=4.0, resolution=(1080, 1080)) -> str | None:
    try:
        # 1. التحقق من الصور
        image_files = sorted([f for f in IMAGES_DIR.glob("*.png")])
        if not image_files:
            raise Exception("❌ لا توجد صور داخل ai_images/outputs/")
        
        print(f"📸 عدد الصور الموجودة: {len(image_files)}")

        # 2. تجهيز المقاطع من الصور
        clips = []
        for image_file in image_files:
            print(f"🖼 معالجة الصورة: {image_file}")
            clip = ImageClip(str(image_file)).set_duration(image_duration)
            clip = clip.resize(height=resolution[1])
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # 3. دمج الصوت
        if AUDIO_PATH.exists() and AUDIO_PATH.stat().st_size > 1000:
            print(f"🔊 إضافة الصوت: {AUDIO_PATH}")
            audio = AudioFileClip(str(AUDIO_PATH))
            video = video.set_audio(audio)
        else:
            print("⚠ ملف الصوت غير موجود أو حجمه غير كافٍ، سيتم إنشاء الفيديو بدون صوت.")

        # 4. اسم الفيديو
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = VIDEO_OUTPUT_DIR / f"final_video_{timestamp}.mp4"

        # 5. حفظ الفيديو
        print(f"💾 حفظ الفيديو في: {output_path}")
        video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )

        if not output_path.exists():
            raise Exception("⚠ تم حفظ الفيديو لكن لم يتم العثور على الملف الناتج!")

        return str(output_path)

    except Exception as e:
        print(f"🔥 خطأ أثناء تركيب الفيديو: {e}")
        return None
