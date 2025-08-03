# main.py

from content_studio.generate_script.script_generator import generate_script

def generate_video_from_topic(topic: str, lang: str = "english", tone: str = "emotional") -> dict:
    """
    نقطة الدخول الأساسية لأي وكيل: توليد سكربت (لاحقًا: صوت + صور + فيديو)
    الآن فقط يولّد سكربت ويرجعه كنص.
    """
    script_text = generate_script(topic, tone=tone, lang=lang)

    return {
        "topic": topic,
        "script": script_text,
        "lang": lang,
        "tone": tone,
        "status": "script_ready"
    }

# مثال تجريبي لتشغيل الملف يدويًا
if _name_ == "_main_":
    topic = "Why most people quit sports after 2 weeks"
    result = generate_video_from_topic(topic)
    print("\n===== TOPIC =====")
    print(result["topic"])
    print("\n===== SCRIPT =====")
    print(result["script"])
