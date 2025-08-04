# script_writer.py

def generate_script_from_traits(user_data: dict, lang: str = "en") -> str:
    full_text = user_data.get("full_text", "")
    video_type = user_data.get("video_type", "🎞 مقطع طويل")

    # توليد سكربت بناءً على نوع الفيديو
    if video_type == "🎞 مقطع طويل":
        script = generate_long_form_script(full_text, lang)
    elif video_type == "🎯 اقتباس قصير":
        script = generate_short_quote_script(full_text, lang)
    elif video_type == "📢 إعلان تجريبي":
        script = generate_teaser_ad_script(full_text, lang)
    else:
        script = generate_long_form_script(full_text, lang)  # النوع الافتراضي

    return script


# ⬇ دوال مخصصة لكل نوع فيديو

def generate_long_form_script(text: str, lang: str) -> str:
    return f"""[Long Form Script in {lang.upper()}]

Welcome to a deep journey into identity and movement.

{ text.strip() }

Because every athlete has a story — and yours is just beginning.
"""

def generate_short_quote_script(text: str, lang: str) -> str:
    quote = text.strip().split(".")[0]
    return f"""[Short Quote Format – {lang.upper()}]

"{quote}"

This is your reminder: you are built for more. ⚡
"""

def generate_teaser_ad_script(text: str, lang: str) -> str:
    return f"""[Teaser Ad Format – {lang.upper()}]

What if your drive had a sport?
What if your story had a field?

{ text.strip() }

This is SportSync AI. Your movement begins now.
"""
