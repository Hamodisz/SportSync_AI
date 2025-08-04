# agents/marketing/video_pipeline/image_generator.py

import os

def generate_images_from_script(script_text: str) -> list:
    """
    توليد صور تمثّل مشاهد من السكربت النصي.
    حاليًا نولد مسارات وهمية لكل جملة.
    """
    image_paths = []
    sentences = [s.strip() for s in script_text.split(".") if s.strip()]
    
    for i, sentence in enumerate(sentences):
        # لاحقًا: يمكن ربط هذا مع نموذج توليد صور فعلي مثل DALL·E أو StableDiffusion
        filename = f"generated_images/scene_{i+1}.png"
        image_paths.append(filename)
    
    return image_paths
