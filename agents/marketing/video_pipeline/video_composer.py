from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, AudioFileClip

def compose_video(image_path, voice_path, output_path="final_video.mp4", duration=10):
    """
    توليد فيديو نهائي بدمج الصورة والصوت مع نص بسيط.
    """
    # صورة ثابتة لفيديو
    img_clip = VideoFileClip(image_path).set_duration(duration)

    # صوت
    audio = AudioFileClip(voice_path)

    # نص فوق الصورة
    txt_clip = TextClip("SportSync AI", fontsize=50, color='white', font='Arial-Bold')
    txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(duration)

    # الدمج النهائي
    video = CompositeVideoClip([img_clip, txt_clip])
    video = video.set_audio(audio)

    # الحفظ
    video.write_videofile(output_path, fps=24)

    return output_path
