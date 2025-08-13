# app_streamlit.py
# -- coding: utf-8 --
# V1: نص → صور Placeholder (AR/EN) → gTTS (اختياري) → فيديو MP4
# ملف واحد مستقل، لا يعتمد على بقية المشروع. هدفه يطلع نتيجة الآن.

from _future_ import annotations
import os, io, re, base64, traceback, uuid, shutil
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

# دعم العربية
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_AR = True
except Exception:
    HAS_AR = False

st.set_page_config(page_title="SportSync V1", layout="centered")
st.title("🎬 SportSync Video Maker — V1 (Instant)")

# مسارات عمل مؤقتة (آمنة على Render/السيرفرات)
ROOT = Path("/tmp/sportsync_v1")
for p in [ROOT, ROOT/"images", ROOT/"voice", ROOT/"video"]:
    p.mkdir(parents=True, exist_ok=True)

# خطوط (لو عندك ملف داخل المشروع assets/DejaVuSans.ttf يلتقطه تلقائيًا)
FONTS_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    str((Path(_file_).parent / "assets" / "DejaVuSans.ttf").resolve()),
]

def pick_font(size: int = 40):
    for p in FONTS_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def shape_ar(s: str) -> str:
    if not HAS_AR:
        return s
    try:
        return get_display(arabic_reshaper.reshape(s))
    except Exception:
        return s

def wrap_lines(text: str, max_len: int = 28):
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

def make_placeholder(text: str, idx: int, lang: str, out_dir: Path, size=(1024,1024)) -> Path:
    img = Image.new("RGB", size, (20,24,28))
    d = ImageDraw.Draw(img)
    font_big  = pick_font(64)
    font_body = pick_font(40)

    title = f"Scene {idx+1}" if lang == "en" else shape_ar(f"المشهد {idx+1}")
    d.text((40,40), title, fill=(245,245,245), font=font_big)

    body = text if lang == "en" else shape_ar(text)
    y = 140
    for ln in wrap_lines(body, 28)[:12]:
        d.text((40,y), ln, fill=(220,220,220), font=font_body)
        y += 52

    # علامة مائية خفيفة
    wm = "SportSync"
    d.text((size[0]-220, size[1]-60), wm, fill=(180,180,180), font=font_body)

    out = out_dir / f"scene_{idx+1}.png"
    img.save(out, "PNG")
    return out

# واجهة مبسّطة
default_script = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""

with st.form("v1_form"):
    lang = st.selectbox("Language", ["en", "ar"], index=0)
    script = st.text_area("Script (AR/EN)", default_script, height=220)
    secs = st.slider("Seconds per image", 2, 8, 4)
    use_voice = st.checkbox("Add voice-over (gTTS)", value=True)
    bg_music = st.file_uploader("Background music (optional, mp3)", type=["mp3"])
    submit = st.form_submit_button("Generate video", type="primary")

if submit:
    # نظّف مجلد العمل
    for d in ["images", "voice", "video"]:
        target = ROOT / d
        if target.exists():
            for f in target.glob("*"):
                try: f.unlink()
                except: pass

    try:
        # 1) صور
        scenes = extract_scenes(script)
        imgs = [make_placeholder(s, i, lang=lang, out_dir=ROOT/"images") for i, s in enumerate(scenes)]
        st.success(f"✅ Generated {len(imgs)} images")

        # 2) صوت (gTTS) اختياري
        voice_path = None
        if use_voice:
            voice_path = ROOT/"voice"/"final_voice.mp3"
            tts_text = "\n".join(scenes) if lang=="en" else "\n".join([shape_ar(s) for s in scenes])
            try:
                gTTS(tts_text, lang=("ar" if lang=="ar" else "en")).save(str(voice_path))
                st.success("✅ Voice-over saved")
            except Exception as e:
                st.warning(f"⚠ gTTS failed, continue muted: {e}")
                voice_path = None

        # 3) فيديو
        st.info("🎞 Composing video…")
        clips = [ImageClip(str(p)).set_duration(secs) for p in imgs]
        video = concatenate_videoclips(clips, method="compose")

        # موسيقى خلفية (اختياري) + تعليق صوتي
        final_audio = None
        try:
            if bg_music is not None:
                tmp_bg = ROOT/"voice"/"bg.mp3"
                tmp_bg.write_bytes(bg_music.read())
                final_audio = AudioFileClip(str(tmp_bg)).volumex(0.12)
        except Exception as e:
            st.warning(f"Background audio skipped: {e}")

        try:
            if voice_path and Path(voice_path).exists():
                vclip = AudioFileClip(str(voice_path)).volumex(1.0)
                final_audio = vclip if final_audio is None else final_audio.set_duration(vclip.duration).fx(lambda a: a)  # keep instance
                # مزج بسيط: لو عندك CompositeAudioClip فتقدر تدمج الاثنين، لكن MoviePy 1.0.3 أحيانًا مزعج على Render
                # للحفاظ على البساطة، خليه تعليق صوتي فقط أو موسيقى فقط (لو تبغى دمج كامل نفعّله لاحقًا)
                video = video.set_audio(vclip)
            elif final_audio is not None:
                video = video.set_audio(final_audio)
        except Exception as e:
            st.warning(f"Audio attach skipped: {e}")

        out_path = ROOT/"video"/"final_video.mp4"
        (ROOT/"video").mkdir(parents=True, exist_ok=True)
        video.write_videofile(str(out_path), fps=24, codec="libx264", audio_codec="aac")

        b = out_path.read_bytes()
        st.video(io.BytesIO(b))
        st.download_button("⬇ Download MP4", b, file_name="final_video.mp4", mime="video/mp4")
        st.success("✅ Done")

    except Exception as e:
        st.error(f"💥 Error: {e}")
        st.code(traceback.format_exc())
