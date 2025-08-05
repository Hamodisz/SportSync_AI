import logging

def generate_ai_video(user_data: dict, lang: str = "en") -> str:
    logging.debug("🚀 Starting generate_ai_video")

    try:
        from content_studio.generate_script.script_generator import generate_script
        from content_studio.ai_images.image_generator import generate_images
        from content_studio.ai_voice.voice_generator import generate_voiceover
        from content_studio.ai_video.video_composer import compose_video_from_assets

        # 1. توليد السكربت
        topic = user_data.get("topic", "Default topic based on user traits")
        tone = user_data.get("tone", "emotional")
        script = generate_script(topic, tone=tone, lang=lang)
        logging.debug(f"📝 Script generated:\n{script}")

        # 2. توليد الصور
        image_paths = generate_images(script, lang)
        logging.debug(f"🖼 Image paths: {image_paths}")

        # 3. توليد الصوت
        audio_path = generate_voiceover(script, lang)
        logging.debug(f"🎙 Voiceover path: {audio_path}")

        # 4. دمج الفيديو
        final_video_path = compose_video_from_assets()
        logging.debug(f"🎬 Final video path: {final_video_path}")

        return final_video_path

    except Exception as e:
        logging.error(f"❌ Error in generate_ai_video: {e}")
        return ""

    finally:
        logging.debug("✅ Ending generate_ai_video")
