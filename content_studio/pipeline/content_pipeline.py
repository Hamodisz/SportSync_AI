# content_pipeline.py

from content_studio.generate_script.script_generator import generate_script
from content_studio.ai_images.generate_images import generate_images
from content_studio.ai_voice.voice_generator import generate_voice_from_script
from content_studio.ai_video.video_composer import compose_video_from_assets
from content_studio.config.style_loader import get_style_for_topic

def run_full_pipeline(topic: str, lang: str = "english", tone: str = "emotional") -> dict:
    """
    يشغل كل مراحل الإنتاج: سكربت → صور → صوت → فيديو
    """
    print(f"\n🎯 الموضوع: {topic}")
    style = get_style_for_topic(topic)
    
    # تحويل اللغة للصيغة الصحيحة
    lang_code = "en" if lang.lower().startswith("en") else "ar"

    # 1. توليد السكربت
    print("✏️ توليد السكربت...")
    script = generate_script(topic, tone=tone, lang=lang)

    # 2. توليد الصور
    print("🖼️ توليد الصور...")
    image_paths = generate_images(script, lang=lang_code, use_runpod=False)

    # 3. توليد الصوت
    print("🔊 توليد الصوت...")
    audio_path = generate_voice_from_script(script, lang=lang_code)

    # 4. تركيب الفيديو
    print("🎞️ تركيب الفيديو...")
    video_path = compose_video_from_assets(
        voice_path=audio_path,
        image_duration=3.0,
        aspect="portrait"
    )

    return {
        "topic": topic,
        "script": script,
        "images": image_paths,
        "audio": audio_path,
        "video": video_path,
        "style": style
    }

# اختبار مباشر
if __name__ == "__main__":
    result = run_full_pipeline("Why most people give up on fitness")
    print("\n✅ تم إنتاج الفيديو النهائي:")
    print(result["video"])
