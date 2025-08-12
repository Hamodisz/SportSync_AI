# -*- coding: utf-8 -*-
from pathlib import Path
from gtts import gTTS

VOICE_DIR = Path("content_studio/ai_voice/voices/")
VOICE_DIR.mkdir(parents=True, exist_ok=True)
VOICE_PATH = VOICE_DIR / "final_voice.mp3"

def generate_voice_from_script(script: str, lang: str = "en") -> str:
    lang_code = "en" if lang.lower().startswith("en") else "ar"
    # خفّض النص لتجاوز قيود gTTS
    text = script.replace("\n\n", ". ").replace("\n", " ")
    if len(text) > 4000:
        text = text[:4000]
    tts = gTTS(text=text, lang=lang_code)
    tts.save(str(VOICE_PATH))
    return str(VOICE_PATH)
