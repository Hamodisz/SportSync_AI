import logging

from content_studio.ai_video.script_writer import generate_script_from_traits
from content_studio.ai_video.image_generator import generate_images
from content_studio.ai_video.voice_generator import generate_voiceover
from content_studio.ai_video.video_composer import compose_video_from_assets

def generate_ai_video(user_data: dict, lang: str = "en") -> str:
    logging.debug("🚀 Starting generate_ai_video")

    try:
        # ✏ توليد السكربت من السمات
        script = generate_script_from_traits(user_data, lang)
        logging.debug(f"📜 Generated script:\n{script}")

        # 🖼 توليد الصور
        image_paths = generate_images(script, lang)
        logging.debug(f"🖼 Generated image paths: {image_paths}")

        # 🎙 توليد الصوت
        audio_path = generate_voiceover(script, lang)
        logging.debug(f"🎙 Generated voiceover path: {audio_path}")

        # 🎬 تركيب الفيديو
        final_video_path = compose_video_from_assets(image_paths, audio_path, lang)
        logging.debug(f"🎬 Final video path: {final_video_path}")

        return final_video_path

    except Exception as e:
        logging.error(f"❌ Error in generate_ai_video: {e}")
        return ""

    finally:
        logging.debug("✅ Ending generate_ai_video")
