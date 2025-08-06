# content_studio/ai_voice/voice_generator.py

import os
import requests
from pathlib import Path
import logging

# 🧠 إعدادات عامة
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "your-eleven-api-key-here")  # يُفضل استخدام env
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # يمكنك تغييره حسب الصوت المفضل
VOICE_OUTPUT = Path("content_studio/ai_voice/voices/final_voice.mp3")

# 🔐 تأكد من وجود المجلد
VOICE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def generate_voice_from_script(script_text: str, voice_id: str = VOICE_ID) -> str:
    """
    🎙 يحوّل نص مكتوب إلى صوت باستخدام ElevenLabs API ويُخزن كـ MP3.

    Args:
        script_text (str): النص المطلوب تحويله إلى صوت.
        voice_id (str): معرّف الصوت من ElevenLabs.

    Returns:
        str: المسار الكامل لملف الصوت الناتج.
    
    Raises:
        Exception: في حال فشل الاتصال أو الرد من API.
    """
    logging.debug("🚀 بدء توليد الصوت من النص")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": script_text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        with open(VOICE_OUTPUT, "wb") as f:
            f.write(response.content)
        logging.info(f"✅ تم توليد الصوت في: {VOICE_OUTPUT}")
        return str(VOICE_OUTPUT)
    else:
        error_msg = f"❌ فشل في توليد الصوت: {response.status_code} - {response.text}"
        logging.error(error_msg)
        raise Exception(error_msg)

# 🧪 مثال مباشر (تشغيل يدوي)
if _name_ == "_main_":
    sample_script = "Welcome to the future of sports and AI."
    try:
        output_path = generate_voice_from_script(sample_script)
        print(f"✅ صوت محفوظ في: {output_path}")
    except Exception as e:
        print(f"🔥 فشل التوليد: {e}")
