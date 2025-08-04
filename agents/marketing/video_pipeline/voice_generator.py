import os
import tempfile
from gtts import gTTS  # يمكنك استبداله بمحرك TTS أقوى مثل ElevenLabs لاحقًا

def generate_voiceover(text, lang='ar'):
    """
    توليد صوت الراوي من النص باستخدام Google TTS وحفظه مؤقتًا
    """
    tts = gTTS(text=text, lang=lang)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)

    return temp_file.name
