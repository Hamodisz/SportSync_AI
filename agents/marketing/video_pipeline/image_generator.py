# agents/marketing/video_pipeline/image_generator.py

import os
from PIL import Image, ImageDraw, ImageFont

def generate_images_from_script(script_text: str) -> list:
    """
    توليد صور تمثّل مشاهد من السكربت النصي.
    (حالياً: توليد صور وهمية تحتوي على النص)
    """
    image_paths = []
    sentences = [s.strip() for s in script_text.split(".") if s.strip()]
    
    os.makedirs("generated_images", exist_ok=True)

    for i, sentence in enumerate(sentences):
        filename = f"generated_images/scene_{i+1}.png"
        
        img = Image.new('RGB', (1280, 720), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.text((50, 300), sentence, fill=(255, 255, 255))  # نرسم الجملة على الصورة
        
        img.save(filename)
        image_paths.append(filename)
    
    return image_paths
