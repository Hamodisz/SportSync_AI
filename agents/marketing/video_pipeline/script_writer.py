from .script_writer import generate_script
from .image_generator import generate_images
from .voice_generator import generate_voiceover
from .video_composer import compose_video
from .publish_scheduler import schedule_publish

def run_full_pipeline(user_data, lang="ar"):
    """
    تشغيل خط إنتاج الفيديو بالكامل: نص → صورة → صوت → فيديو → جدول نشر
    """
    script = generate_script(user_data, lang=lang)
    images = generate_images(script)
    voice_path = generate_voiceover(script, lang=lang)
    final_video = compose_video(images, voice_path)
    schedule_publish(final_video, user_data)
    return final_video
