import logging

def generate_ai_video(user_data: dict, lang: str = "en") -> str | None:
    logging.debug("🚀 Starting generate_ai_video")

    try:
        from agents.marketing.video_pipeline.script_writer import generate_script_from_traits
        from agents.marketing.video_pipeline.image_generator import generate_images
        from agents.marketing.video_pipeline.voice_generator import generate_voiceover
        from content_studio.ai_video.video_composer import compose_video_from_assets

        # 1. كتابة السكربت
        script = generate_script_from_traits(user_data, lang)
        logging.debug(f"📜 Script generated:\n{script}")

        # 2. توليد الصور
        image_paths = generate_images(script, lang)
        logging.debug(f"🖼 Image paths: {image_paths}")

        # 3. توليد الصوت
        audio_path = generate_voiceover(script, lang)
        logging.debug(f"🎙 Voiceover path: {audio_path}")

        # 4. توليد الفيديو من الملفات
        final_video_path = compose_video_from_assets()
        logging.debug(f"🎞 Final video path: {final_video_path}")

        if not final_video_path:
            raise ValueError("❌ compose_video_from_assets لم يرجع مسار فيديو صالح")

        return final_video_path

    except Exception as e:
        logging.error(f"❌ Error in generate_ai_video: {e}")
        return None

    finally:
        logging.debug("✅ Ending generate_ai_video")
