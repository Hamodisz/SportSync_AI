# -- coding: utf-8 --
import os, re, base64, tempfile
from pathlib import Path
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS

ROOT       = Path(".")
IMAGES_DIR = ROOT / "content_studio/ai_images/outputs"
VOICE_DIR  = ROOT / "content_studio/ai_voice/voices"
FINAL_DIR  = ROOT / "content_studio/ai_video/final_videos"
for p in (IMAGES_DIR, VOICE_DIR, FINAL_DIR):
    p.mkdir(parents=True, exist_ok=True)

def extract_scenes(txt: str):
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)", txt, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", txt) if p.strip()]
    return scenes[:6] if scenes else [txt.strip()[:140]]

def wrap_lines(text, max_len=30):
    words = text.split()
    out, line = [], ""
    for w in words:
        if len((line + " " + w).strip()) <= max_len:
            line = (line + " " + w).strip()
        else:
            out.append(line); line = w
    if line: out.append(line)
    return out

def make_placeholder(text, idx, size=(1024,1024)):
    img = Image.new("RGB", size, (20,24,28))
    d = ImageDraw.Draw(img)
    try:
        # على معظم الصور الرسمية ما فيه خطوط TTF، لذلك خلّينا الافتراضي
        font_big  = ImageFont.load_default()
        font_body = ImageFont.load_default()
    except Exception:
        font_big  = ImageFont.load_default()
        font_body = ImageFont.load_default()
    d.text((40,40), f"Scene {idx+1}", fill=(245,245,245), font=font_big)
    y = 140
    for ln in wrap_lines(text, 30)[:12]:
        d.text((40,y), ln, fill=(220,220,220), font=font_body); y += 24
    out = IMAGES_DIR / f"scene_{idx+1}.png"
    img.save(out, "PNG")
    return str(out)

st.set_page_config(page_title="SportSync - Demo", page_icon="🎬", layout="centered")
st.title("🎬 SportSync — Quick Video Demo")

default_script = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""
script = st.text_area("Script (EN/AR):", value=default_script, height=240)
col1, col2, col3 = st.columns(3)
with col1:
    per_image = st.number_input("Seconds / image",  value=4, min_value=1, max_value=20, step=1)
with col2:
    fps = st.number_input("FPS", value=24, min_value=10, max_value=60, step=1)
with col3:
    use_voice = st.checkbox("Add voice (gTTS)", value=True)

if st.button("Generate video"):
    # نظّف الصور القديمة
    for f in IMAGES_DIR.glob("*"):
        try: f.unlink()
        except: pass

    scenes = extract_scenes(script)
    paths = [make_placeholder(s, i) for i, s in enumerate(scenes)]
    st.write("✅ Images:", paths)

    voice_path = None
    if use_voice:
        try:
            VOICE_DIR.mkdir(parents=True, exist_ok=True)
            voice_path = str(VOICE_DIR / "final_voice.mp3")
            gTTS("\n".join(scenes), lang="en").save(voice_path)
            st.write("✅ Voice:", voice_path)
        except Exception as e:
            st.warning(f"gTTS failed, muted video. ({e})")
            voice_path = None

    clips = [ImageClip(p).set_duration(per_image) for p in paths]
    video = concatenate_videoclips(clips, method="compose")
    if voice_path and Path(voice_path).exists():
        video = video.set_audio(AudioFileClip(voice_path))

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FINAL_DIR / "final_video.mp4"
    video.write_videofile(str(out_path), fps=fps, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    st.success(f"Saved: {out_path}")
    st.video(str(out_path))

    with open(out_path, "rb") as f:
        st.download_button("⬇ Download MP4", f, file_name="final_video.mp4", mime="video/mp4")
