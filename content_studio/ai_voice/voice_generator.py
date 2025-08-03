# voice_generator.py

import os
import requests
from pathlib import Path

ELEVEN_API_KEY = "your-eleven-api-key-here"  # غيّرها لو عندك env

VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # الصوت الافتراضي (يمكن تغييره)
VOICE_OUTPUT = Path("content_studio/ai_voice/voices/final_voice.mp3")
VOICE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def generate_voice_from_script(script_text: str, voice_id=VOICE_ID) -> str:
    """
    يولد صوت من نص باستخدام ElevenLabs API ويحفظه كـ mp3
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": script_text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        with open(VOICE_OUTPUT, "wb") as f:
            f.write(response.content)
        return str(VOICE_OUTPUT)
    else:
        raise Exception(f"❌ خطأ في توليد الصوت: {response.status_code} - {response.text}")

# مثال تشغيل مباشر
if _name_ == "_main_":
    from content_studio.generate_script.script_generator import generate_script
    script = generate_script("Why do people quit sports?")
    path = generate_voice_from_script(script)
    print(f"✅ تم توليد الصوت في: {path}")
