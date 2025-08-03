def generate_images(script_text):
    """
    توليد صور باستخدام نموذج ذكاء اصطناعي بناءً على السكربت.
    """
    # للتبسيط، نعيد مسارات صور وهمية حالياً
    image_paths = []
    for i, sentence in enumerate(script_text.split(".")):
        if sentence.strip():
            image_paths.append(f"generated_images/scene_{i+1}.png")
    return image_paths
