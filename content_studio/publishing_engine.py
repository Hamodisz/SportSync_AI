import os
import re
import json
import datetime
from pathlib import Path
import openai
import requests
import tempfile
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

openai.api_key = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

def generate_with_gpt(prompt, temperature=0.7):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content.strip()

# ---------- النصوص ----------
def generate_video_title(script_text):
    prompt = f"""Generate a compelling YouTube video title under 70 characters:
\"\"\"{script_text}\"\"\""""
    return generate_with_gpt(prompt)

def generate_video_description(script_text):
    prompt = f"""Write a short YouTube video description under 500 characters:
\"\"\"{script_text}\"\"\""""
    return generate_with_gpt(prompt)

def generate_keywords(script_text, max_keywords=10):
    prompt = f"""Extract {max_keywords} SEO keywords for YouTube from:
\"\"\"{script_text}\"\"\""""
    return [kw.strip() for kw in generate_with_gpt(prompt).split(",") if kw.strip()]

def extract_shorts(script_text, count=5):
    prompt = f"""Extract {count} short quotes (under 20 seconds when read aloud):
\"\"\"{script_text}\"\"\""""
    return [line.strip("-• ") for line in generate_with_gpt(prompt).split("\n") if line.strip()]

def generate_thumbnail_text(script_text):
    prompt = f"""Generate a short emotional phrase for a YouTube thumbnail:
\"\"\"{script_text}\"\"\""""
    return generate_with_gpt(prompt)

# ---------- صوت ----------
def generate_voice(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"ElevenLabs error: {response.status_code}, {response.text}")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    with open(temp_file.name, "wb") as f:
        f.write(response.content)
    return temp_file.name

# ---------- صورة ----------
def generate_thumbnail_image(thumbnail_text, output_path):
    dalle_prompt = f"A cinematic thumbnail with bold text: {thumbnail_text}, dark background, cinematic lighting"
    response = openai.Image.create(prompt=dalle_prompt, n=1, size="1024x1024")
    image_url = response["data"][0]["url"]
    img_data = requests.get(image_url).content
    with open(output_path, "wb") as f:
        f.write(img_data)

# ---------- فيديو ----------
def create_video(image_path, audio_path, output_path, duration=None):
    audio = AudioFileClip(audio_path)
    duration = duration or audio.duration
    image = ImageClip(image_path).set_duration(duration).set_audio(audio)
    image.write_videofile(output_path, fps=24)

# ---------- التصدير الكامل ----------
def export_video_package(script_text, index=1):
    today = datetime.date.today().strftime("%Y_%m_%d")
    folder = Path(f"export/{today}video{index:02d}")
    folder.mkdir(parents=True, exist_ok=True)

    title = generate_video_title(script_text)
    desc = generate_video_description(script_text)
    tags = generate_keywords(script_text)
    thumbnail_text = generate_thumbnail_text(script_text)
    shorts = extract_shorts(script_text)

    # Save metadata
    (folder / "long_script.txt").write_text(script_text, encoding="utf-8")
    (folder / "title.txt").write_text(title, encoding="utf-8")
    (folder / "description.txt").write_text(desc, encoding="utf-8")
    (folder / "tags.txt").write_text(", ".join(str(x) for x in tags), encoding="utf-8")
    (folder / "thumbnail_text.txt").write_text(thumbnail_text, encoding="utf-8")

    # Shorts
    shorts_dir = folder / "shorts"
    shorts_dir.mkdir(exist_ok=True)
    for i, q in enumerate(shorts, 1):
        (shorts_dir / f"short_{i:02d}.txt").write_text(q, encoding="utf-8")

    # Generate thumbnail image
    thumbnail_path = folder / "thumbnail.jpg"
    generate_thumbnail_image(thumbnail_text, thumbnail_path)

    # Generate voice
    voice_path = generate_voice(script_text)
    final_audio_path = folder / "voice.mp3"
    os.rename(voice_path, final_audio_path)

    # Generate video
    video_path = folder / "video.mp4"
    create_video(thumbnail_path, final_audio_path, video_path)

    # Generate shorts videos
    for i, q in enumerate(shorts, 1):
        short_audio = generate_voice(q)
        short_video_path = shorts_dir / f"short_{i:02d}.mp4"
        create_video(thumbnail_path, short_audio, short_video_path)

    print(f"\n✅ Video package ready: {folder}")
    return str(folder)
