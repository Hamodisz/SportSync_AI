# style_loader.py

import json
from pathlib import Path

SETTINGS_FILE = Path("content_studio/config/settings.json")

with open(SETTINGS_FILE, "r") as f:
    SETTINGS = json.load(f)

def get_style_for_topic(topic: str) -> dict:
    topic = topic.lower()

    if any(word in topic for word in ["motivation", "push", "overcome"]):
        return SETTINGS["styles"]["motivational"]
    elif any(word in topic for word in ["meaning", "soul", "life"]):
        return SETTINGS["styles"]["philosophical"]
    elif any(word in topic for word in ["how to", "steps", "guide"]):
        return SETTINGS["styles"]["educational"]

    # الافتراضي
    return {
        "image_style": SETTINGS["default_style"],
        "video_style": "cinematic",
        "voice_style": "standard"
    }
