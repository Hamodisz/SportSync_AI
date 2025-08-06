# run_full_generation.py

import os
from pathlib import Path
from content_studio.generate_script.script_generator import generate_script
from agents.marketing.visual_cue_generator import inject_visual_guidance
from content_studio.ai_images.generate_images import generate_images_from_script
from content_studio.ai_voice.voice_generator import generate_voice_from_script
from content_studio.ai_video.video_composer import compose_video_from_assets

# --- إعداد ---
topic = "Why do people quit sports?"
tone = "emotional"

# --- 1. توليد السكربت ---
print("📝 Generating script...")
raw_script = generate_script(topic=topic, tone=tone)

# --- 2. حقن visual cues ---
print("🎬 Injecting visual cues...")
scenes = raw_script.split("\n")
enhanced_scenes = inject_visual_guidance(scenes)
final_script = "\n".join(enhanced_scenes)

# --- 3. توليد الصور ---
print("🖼 Generating images...")
generate_images_from_script(final_script, image_style="cinematic-realistic")

# --- 4. توليد الصوت (gTTS) ---
print("🎤 Generating voiceover...")
generate_voice_from_script(final_script)

# --- 5. دمج الفيديو ---
print("🎞 Composing video...")
video_path = compose_video_from_assets(image_duration=4.0, resolution=(1080, 1080))

if video_path:
    print(f"✅ الفيديو جاهز: {video_path}")
else:
    print("❌ فشل في التوليد.")
