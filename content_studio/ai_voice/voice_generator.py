# voice_generator.py

import os
from pathlib import Path
from gtts import gTTS
import logging

# 📁 تحديد مكان حفظ الصوت
VOICE_OUTPUT = Path("content_studio/ai_voice/voices/final_voice.mp3")
VOICE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def generate_voice_from_script(script_text: str, lang: str = "en") -> str:
    """
    🎤 توليد صوت من نص باستخدام gTTS (مجاني بالكامل)
    """
    try:
        logging.debug("🔊 بدء توليد الصوت باستخدام gTTS")
        logging.debug(f"📜 النص:\n{script_text}")
        logging.debug(f"🌍 اللغة: {lang}")

        tts = gTTS(text=script_text, lang=lang)
        tts.save(str(VOICE_OUTPUT))

        logging.debug(f"✅ تم حفظ الصوت في: {VOICE_OUTPUT}")
        return str(VOICE_OUTPUT)

    except Exception as e:
        logging.error(f"❌ خطأ أثناء توليد الصوت: {e}")
        return None

# 🧪 اختبار مباشر
if _name_ == "_main_":
    text = "مرحبًا بك في نظام سبورت سنك. هذا هو اختبار توليد الصوت."
    path = generate_voice_from_script(text, lang="ar")
    print(f"✅ الملف الناتج: {path}")
