# video_composer.py

import os
from pathlib import Path
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
AUDIO_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
VIDEO_OUTPUT_PATH = Path("content_studio/ai_video/final_videos/final_video.mp4")

def compose_video_from_assets(image_duration=4.0, resolution=(1080, 1080)):
    """
    يدمج الصور مع الصوت ويخرج فيديو موحّد.
    """
    # 1. جلب الصور وترتيبها
    image_files = sorted([f for f in IMAGES_DIR.glob("*.png")])
    if not image_files:
        raise Exception("❌ لا توجد صور داخل ai_images/outputs/")

    clips = []
    for image_file in image_files:
        clip = ImageClip(str(image_file)).set_duration(image_duration)
        clip = clip.resize(height=resolution[1])
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    # 2. دمج الصوت (اختياري الآن)
    if AUDIO_PATH.exists():
        audio = AudioFileClip(str(AUDIO_PATH))
        video = video.set_audio(audio)

    # 3. تصدير الفيديو النهائي
    VIDEO_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(str(VIDEO_OUTPUT_PATH), fps=24)

    return str(VIDEO_OUTPUT_PATH)

# مثال تشغيل مباشر
if _name_ == "_main_":
    path = compose_video_from_assets()
    print(f"✅ الفيديو جاهز: {path}")
