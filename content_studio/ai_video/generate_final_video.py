# file: content_studio/ai_video/generate_final_video.py
import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from gtts import gTTS

# مسار حفظ الفيديوهات النهائية
FINAL_DIR = "content_studio/ai_video/final_videos"
os.makedirs(FINAL_DIR, exist_ok=True)

def generate_final_video(video_paths, narration_text, output_name="final_video.mp4"):
    """
    يدمج مقاطع الفيديو + يضيف تعليق صوتي + يحفظ النتيجة النهائية
    """
    if not video_paths:
        raise ValueError("قائمة الفيديوهات فارغة.")

    # 1) دمج المقاطع
    clips = []
    try:
        for v in video_paths:
            if not os.path.exists(v):
                raise FileNotFoundError(f"لم يتم العثور على الملف: {v}")
            clips.append(VideoFileClip(v).resize((1280, 720)))

        final_clip = concatenate_videoclips(clips, method="compose")

        # 2) إنشاء التعليق الصوتي من النص
        audio_path = os.path.join(FINAL_DIR, "narration.mp3")
        tts = gTTS(text=narration_text, lang="ar")
        tts.save(audio_path)

        # 3) إضافة التعليق الصوتي للفيديو
        narration_audio = AudioFileClip(audio_path)
        final_clip = final_clip.set_audio(narration_audio)

        # 4) حفظ الفيديو النهائي
        output_path = os.path.join(FINAL_DIR, output_name)
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4
        )

        print(f"✅ الفيديو النهائي جاهز: {output_path}")
        return output_path

    finally:
        # تنظيف الموارد
        try:
            for c in clips:
                c.close()
        except Exception:
            pass
        try:
            if 'narration_audio' in locals():
                narration_audio.close()
        except Exception:
            pass
        try:
            if 'final_clip' in locals():
                final_clip.close()
        except Exception:
            pass


if __name__ == "__main__":
    # مثال تشغيل
    video_files = [
        "content_studio/ai_video/temp/video1.mp4",
        "content_studio/ai_video/temp/video2.mp4"
    ]
    narration = "مرحباً بكم في الفيديو التجريبي من نظام Sport Sync AI."
    generate_final_video(video_files, narration)
