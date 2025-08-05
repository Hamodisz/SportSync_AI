def generate_video_keywords(script_text: str, traits: dict, video_type: str = "") -> list:
    """
    توليد كلمات مفتاحية ذكية من السكربت والسمات الشخصية
    """
    keywords = set()

    # 1. من السمات
    for k, v in traits.items():
        if isinstance(v, str) and len(v) < 30:
            keywords.add(v.lower())
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str) and len(item) < 30:
                    keywords.add(item.lower())

    # 2. من السكربت – كلمات متكررة قوية
    for word in script_text.lower().split():
        if word.isalpha() and len(word) > 4:
            keywords.add(word)

    # 3. من نوع الفيديو
    if "quote" in video_type.lower():
        keywords.add("shorts")
        keywords.add("inspiration")
    elif "long" in video_type.lower():
        keywords.add("deep dive")
        keywords.add("storytelling")
    elif "ad" in video_type.lower():
        keywords.add("trailer")
        keywords.add("teaser")

    return sorted(list(keywords))[:15]  # نختار فقط أهم 15 كلمة
