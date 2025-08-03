import os
import tempfile
from gtts import gTTS  # يمكنك استبداله بأي محرك TTS آخر مثل ElevenLabs API

def generate_voice(text, lang='ar'):
    """
    توليد صوت من نص باستخدام Google TTS وحفظه مؤقتًا
    """
    tts = gTTS(text=text, lang=lang)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)

    return temp_file.name
