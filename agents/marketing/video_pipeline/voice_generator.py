# agents/marketing/video_pipeline/voice_generator.py

import os
import tempfile
from gtts import gTTS  # يمكن استبداله لاحقًا بمحرك أكثر احترافية

def generate_voiceover(script_text: str, lang: str = "ar") -> str:
    """
    توليد صوت الراوي من السكربت النصي وحفظه مؤقتًا
    """
    tts = gTTS(text=script_text, lang=lang)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)

    return temp_file.name
