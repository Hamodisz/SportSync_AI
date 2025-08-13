# app_streamlit.py
# Streamlit one-page pipeline: Script -> Placeholder images -> (gTTS) -> Video preview
import os, io, re, base64, traceback, tempfile, uuid
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# صوت
from gtts import gTTS
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

# العربية
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="SportSync Maker", layout="centered")
st.title("🎬 SportSync – quick video maker (Render)")

# ---------- إعدادات ----------
TMP_ROOT = Path("/tmp/sportsync")
TMP_ROOT.mkdir(parents=True, exist_ok=True)

# خط يدعم العربية (حط الملف داخل repo لو تبي ثابت):
FALLBACK_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # عادة متوفر
    str((Path(_file_).parent / "assets" / "DejaVuSans.ttf").resolve()),  # إن رفعت الخط معك
]

def pick_font(size: int = 40) -> ImageFont.FreeTypeFont:
    for p in FALLBACK_FONTS:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def shape_ar_text(s: str) -> str:
    # تشكيل + اتجاه من اليمين لليسار
    try:
        return get_display(arabic_reshaper.reshape(s))
    except Exception:
        return s

def wrap_lines(text: str, max_len: int = 26):
    words = text.split()
    out, line = [], ""
    for w in words:
        if len((line + " " + w).strip()) <= max_len:
            line = (line + " " + w).strip()
        else:
            out.append(line); line = w
    if line: out.append(line)
    return out

def extract_scenes(txt: str):
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)", txt, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", txt) if p.strip()]
    return scenes[:8] if scenes else [txt.strip()[:140]]

def make_placeholder(text: str, idx: int, out_dir: Path, lang: str, size=(1024,1024)) -> Path:
    img = Image.new("RGB", size, (20,24,28))
    d = ImageDraw.Draw(img)
    font_big  = pick_font(64)
    font_body = pick_font(40)

    # عنوان
    title = f"Scene {idx+1}" if lang == "en" else shape_ar_text(f"المشهد {idx+1}")
    d.text((40,40), title, fill=(245,245,245), font=font_big)

    # نص
    body = text if lang == "en" else shape_ar_text(text)
    y = 140
    for ln in wrap_lines(body, 28)[:12]:
        d.text((40,y), ln, fill=(220,220,220), font=font_body)
        y += 52

    out = out_dir / f"scene_{idx+1}.png"
    img.save(out, "PNG")
    return out

# ---------- الواجهة ----------
default_script = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""

with st.form("make_form"):
    lang = st.selectbox("Language", ["en", "ar"], index=0)
    script = st.text_area("Script", default_script, height=220)
    use_voice = st.checkbox("Add voice-over (gTTS)", value=True)
    secs = st.slider("Seconds per image", 2, 8, 4)
    submitted = st.form_submit_button("Generate")

if submitted:
    job_id = uuid.uuid4().hex[:8]
    work = TMP_ROOT / job_id
    imgs_dir = work / "images"
    voice_dir = work / "voice"
    video_dir = work / "video"
    for p in (imgs_dir, voice_dir, video_dir):
        p.mkdir(parents=True, exist_ok=True)

    try:
        # 1) صور
        scenes = extract_scenes(script)
        st.info(f"Generating {len(scenes)} placeholder images…")
        image_paths = [make_placeholder(s, i, imgs_dir, lang=lang) for i, s in enumerate(scenes)]
        st.success(f"Images ready: {len(image_paths)}")

        # 2) صوت (اختياري)
        voice_path = None
        if use_voice:
            tts_text = "\n".join(scenes) if lang=="en" else "\n".join([shape_ar_text(s) for s in scenes])
            voice_path = str(voice_dir / "final_voice.mp3")
            try:
                gTTS(tts_text, lang=("ar" if lang=="ar" else "en")).save(voice_path)
                st.success("Voice saved.")
            except Exception as e:
                st.warning(f"gTTS failed, continue muted: {e}")
                voice_path = None

        # 3) فيديو
        st.info("Composing video…")
        clips = [ImageClip(str(p)).set_duration(secs) for p in image_paths]
        video = concatenate_videoclips(clips, method="compose")
        if voice_path and Path(voice_path).exists():
            video = video.set_audio(AudioFileClip(voice_path))

        out_path = video_dir / "final_video.mp4"
        video.write_videofile(str(out_path), fps=24, codec="libx264", audio_codec="aac")
        st.success("Video ready ✅")

        # 4) معاينة + تحميل
        b = out_path.read_bytes()
        st.video(io.BytesIO(b))
        st.download_button("Download MP4", b, file_name="final_video.mp4", mime="video/mp4")

        with st.expander("Debug info"):
            st.json({
                "job_id": job_id,
                "images": [str(p) for p in image_paths],
                "voice": voice_path,
                "video": str(out_path),
            })

    except Exception as e:
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())
