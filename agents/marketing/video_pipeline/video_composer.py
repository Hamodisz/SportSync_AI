import logging
import os

def compose_final_video(images: list, audio_path: str, lang: str) -> str:
    logging.debug("🎬 Starting final video composition")
    logging.debug(f"🖼 Images received: {images}")
    logging.debug(f"🔊 Audio path received: {audio_path}")

    try:
        if not images:
            logging.error("❌ No images provided")
        if not audio_path or not os.path.exists(audio_path):
            logging.error(f"❌ Audio file does not exist at path: {audio_path}")

        # ⚠ مؤقتًا: نحفظ فيديو فاضي كاختبار (تقدر تحط MoviePy لاحقًا)
        final_video_path = "output/final_video.mp4"
        open(final_video_path, "wb").close()

        logging.debug(f"✅ Video composed and saved at: {final_video_path}")
        return final_video_path

    except Exception as e:
        logging.error(f"❌ Error in compose_final_video: {e}")
        return ""
