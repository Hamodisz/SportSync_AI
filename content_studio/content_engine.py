# content_engine.py

from content_studio.pipeline.content_pipeline import run_full_pipeline

def generate_video_from_topic(topic: str, lang: str = "english", tone: str = "emotional") -> dict:
    """
    💡 هذا هو المحرك الأساسي لتوليد فيديو كامل من موضوع.

    1. يولّد سكربت مبني على النبرة واللغة
    2. يولّد صور مناسبة للمشاهد
    3. يولّد صوت بالنبرة المختارة
    4. يدمج كل شيء في فيديو موحّد
    5. يرجّع النتائج النهائية كـ dict منظمة
    """
    return run_full_pipeline(topic=topic, lang=lang, tone=tone)


def generate_script_only(topic: str, lang: str = "english", tone: str = "emotional") -> str:
    """
    📝 توليد السكربت فقط (للاستخدام المستقل أو للبوستات)
    """
    from content_studio.generate_script.script_generator import generate_script
    return generate_script(topic, tone=tone, lang=lang)


def suggest_topic_from_keywords(keywords: list) -> str:
    """
    🧠 بناء موضوع ذكي تلقائي من قائمة مفاتيح (hooks أو سمات)
    """
    base = ", ".join(str(x) for x in keywords)
    return f"How {base} influences your sport identity"


# 🧪 للتجربة اليدوية فقط
if __name__ == "__main__":
    example_topic = "Why most people give up on fitness"
    output = generate_video_from_topic(example_topic)

    print("🎬 VIDEO:", output["video"])
    print("📝 SCRIPT:", output["script"][:300], "...")
