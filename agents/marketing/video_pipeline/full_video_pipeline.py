import logging

def generate_ai_video(user_data: dict, lang: str = "en") -> str:
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("🚀 Starting generate_ai_video")

    try:
        # Step 1: Generate script
        script = generate_script_from_traits(user_data, lang)
        logging.debug(f"🧠 Generated script:\n{script}")

        # Step 2: Generate images
        images = generate_images(script, lang)
        logging.debug(f"🖼 Images generated: {images}")

        # Step 3: Generate voiceover
        voice_path = generate_voiceover(script, lang)
        logging.debug(f"🔊 Voiceover path: {voice_path}")

        # Step 4: Compose final video
        video_path = compose_final_video(images, voice_path, lang)
        logging.debug(f"🎬 Final video path: {video_path}")

        return video_path

    except Exception as e:
        logging.error(f"❌ Error in generate_ai_video: {e}")
        return ""

    finally:
        logging.debug("🏁 Ending generate_ai_video")
