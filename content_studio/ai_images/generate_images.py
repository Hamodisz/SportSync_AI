# generate_images.py

import os
import re
import openai
from pathlib import Path
from PIL import Image
from io import BytesIO

# إعداد API من البيئة
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

OUTPUT_DIR = Path("content_studio/ai_images/outputs/")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_scenes(script_text: str):
    scenes = re.split(r"Scene\s*#\d+:?", script_text, flags=re.IGNORECASE)
    return [s.strip() for s in scenes if s.strip()]

def generate_image_for_scene(scene_description: str, image_style: str = "realistic", index: int = 0):
    full_prompt = f"{scene_description}. Style: {image_style}. Cinematic lighting."

    response = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    image_data = client.images.download(image_url).read()

    image_path = OUTPUT_DIR / f"scene_{index+1}.png"
    with open(image_path, "wb") as f:
        f.write(image_data)

    return str(image_path)

def generate_images_from_script(script_text: str, image_style: str = "realistic"):
    scenes = extract_scenes(script_text)
    image_paths = []

    for i, scene in enumerate(scenes):
        print(f"🎨 Generating image for Scene #{i+1}...")
        path = generate_image_for_scene(scene, image_style=image_style, index=i)
        image_paths.append(path)

    return image_paths

# ✅ تشغيل مباشر لتجربة السكربت يدويًا
if _name_ == "_main_":
    from content_studio.generate_script.script_generator import generate_script
    script = generate_script("Why do people quit sports?", tone="emotional")
    generate_images_from_script(script, image_style="cinematic-realistic")
