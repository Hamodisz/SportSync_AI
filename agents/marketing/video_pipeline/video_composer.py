import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def compose_final_video(image_paths: list, voice_path: str, output_path: str = "final_videos/ai_composed_video.mp4") -> str:
    """
    دمج الصور والصوت في فيديو نهائي
    """
    clips = []
    duration_per_image = 4  # ثواني لكل صورة

    for path in image_paths:
        clip = ImageClip(path).set_duration(duration_per_image).resize(height=720).set_position("center")
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(voice_path)
    final = video.set_audio(audio)

    # ⛳ تأكد من وجود المجلد
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    final.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path
