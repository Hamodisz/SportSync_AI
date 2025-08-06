# content_studio/ai_voice/voice_generator.py

import os
from pathlib import Path
from gtts import gTTS

# 🛠 إعداد مسار الصوت النهائي
VOICE_OUTPUT = Path("content_studio/ai_voice/voices/final_voice.mp3")
VOICE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def generate_voice_from_script(script_text: str, lang: str = "en") -> str:
    """
    🗣 تحويل نص إلى صوت باستخدام gTTS (Google Text-to-Speech)

    Args:
        script_text (str): النص المطلوب تحويله
        lang (str): اللغة (افتراضي: الإنجليزية)

    Returns:
        str: مسار ملف الصوت الناتج
    """
    try:
        tts = gTTS(text=script_text, lang=lang)
        tts.save(VOICE_OUTPUT)
        print(f"✅ تم حفظ الصوت في: {VOICE_OUTPUT}")
        return str(VOICE_OUTPUT)
    except Exception as e:
        print(f"❌ فشل توليد الصوت: {e}")
        return ""

# ✅ تجربة مباشرة لتوليد الصوت من سكربت بسيط
if _name_ == "_main_":
    sample_script = "Welcome to the future of sports and artificial intelligence."
    generate_voice_from_script(sample_script)
