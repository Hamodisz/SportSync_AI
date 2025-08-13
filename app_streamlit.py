# app_streamlit.py
# -- coding: utf-8 --
import os, io, re, base64, traceback
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

# optional Arabic shaping
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_AR = True
except Exception:
    HAS_AR = False

# imports from our new modules
try:
    from core.personalizer import INTENT_QUESTIONS, build_profile
    from content_studio.generators.script_templates import build_script
    from core.data_store import log_event
except Exception:
    INTENT_QUESTIONS = []
    def build_profile(a): return {"scores":{}, "sport":"running", "tone":"energetic"}
    def build_script(p, lang="en", use_ai=True): 
        return """Title: Your first run today
Scene 1: Lacing shoes — "Every finish line starts with this."
Scene 2: First breath — "Fresh air. Fresh start."
Scene 3: Steps finding rhythm — "Consistency beats perfection."
Outro: 10 minutes. Start now."""
    def log_event(k,d): pass

st.set_page_config(page_title="SportSync", layout="wide")
st.title("🏃‍♂ SportSync — Video + Personalizer (V1.1)")

ROOT = Path("/tmp/sportsync_v1")
IMG_DIR = ROOT/"images"; VOI_DIR = ROOT/"voice"; VID_DIR = ROOT/"video"
for p in (IMG_DIR, VOI_DIR, VID_DIR): p.mkdir(parents=True, exist_ok=True)

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", str(Path("assets/DejaVuSans.ttf").resolve())]
def pick_font(size=40):
    for fp in FONTS:
        if Path(fp).exists():
            try: return ImageFont.truetype(fp, size)
            except Exception: pass
    return ImageFont.load_default()

def shape_ar(s: str) -> str:
    if not HAS_AR: return s
    try: return get_display(arabic_reshaper.reshape(s))
    except Exception: return s

def wrap_lines(text, max_len=28):
    words = text.split(); out, line = [], ""
    for w in words:
        if len((line+" "+w).strip()) <= max_len: line = (line+" "+w).strip()
        else: out.append(line); line = w
    if line: out.append(line)
    return out

def extract_scenes(txt: str):
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)", txt, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", txt) if p.strip()]
    return scenes[:8] if scenes else [txt.strip()[:140]]

def make_placeholder(text, idx, lang, size=(1024,1024)):
    img = Image.new("RGB", size, (20,24,28))
    d = ImageDraw.Draw(img)
    title = f"Scene {idx+1}" if lang=="en" else shape_ar(f"المشهد {idx+1}")
    d.text((40,40), title, fill=(245,245,245), font=pick_font(64))

    body = text if lang=="en" else shape_ar(text)
    y = 140
    for ln in wrap_lines(body, 28)[:12]:
        d.text((40,y), ln, fill=(220,220,220), font=pick_font(40)); y += 52

    out = IMG_DIR / f"scene_{idx+1}.png"
    img.save(out, "PNG"); return out

def compose_video(scenes, lang="en", secs=4, voice=True, bg_music=None):
    # clean
    for d in (IMG_DIR, VOI_DIR, VID_DIR):
        for f in d.glob("*"):
            try: f.unlink()
            except: pass

    # images
    img_paths = [make_placeholder(s, i, lang) for i, s in enumerate(scenes)]
    clips = [ImageClip(str(p)).set_duration(secs) for p in img_paths]
    video = concatenate_videoclips(clips, method="compose")

    # voice
    voice_path = None
    if voice:
        voice_path = VOI_DIR/"final_voice.mp3"
        tts_text = "\n".join(scenes) if lang=="en" else "\n".join([shape_ar(s) for s in scenes])
        try:
            gTTS(tts_text, lang=("ar" if lang=="ar" else "en")).save(str(voice_path))
            video = video.set_audio(AudioFileClip(str(voice_path)))
        except Exception as e:
            st.warning(f"gTTS failed, muted: {e}")

    # bg music (optional)
    if bg_music is not None:
        try:
            AUD = VOI_DIR/"bg.mp3"; AUD.write_bytes(bg_music.read())
            # NOTE: لتبسيط V1.1 نخلي الصوت إمّا تعليق أو موسيقى. دمج كامل نفعّله لاحقاً.
            if voice_path is None:
                video = video.set_audio(AudioFileClip(str(AUD)).volumex(0.15))
        except Exception as e:
            st.warning(f"bg music skipped: {e}")

    # write
    out = VID_DIR/"final_video.mp4"
    video.write_videofile(str(out), fps=24, codec="libx264", audio_codec="aac")
    return out

tab1, tab2 = st.tabs(["⚡ Quick Video", "🧭 Quiz → Sport → Video"])

with tab1:
    st.subheader("Quick Video")
    default_script = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""
    lang = st.selectbox("Language", ["en","ar"], 0, key="qv_lang")
    txt = st.text_area("Script", default_script, height=220)
    secs = st.slider("Seconds per image", 2, 8, 4, key="qv_secs")
    voice = st.checkbox("Add voice-over", True, key="qv_voice")
    bg = st.file_uploader("Background music (mp3, optional)", type=["mp3"], key="qv_bg")
    if st.button("Generate", type="primary"):
        try:
            scenes = extract_scenes(txt)
            out = compose_video(scenes, lang=lang, secs=secs, voice=voice, bg_music=bg)
            data = out.read_bytes()
            st.video(io.BytesIO(data))
            st.download_button("⬇ Download MP4", data, file_name="final_video.mp4", mime="video/mp4")
            log_event("quick_video", {"lang": lang, "scenes": len(scenes)})
        except Exception as e:
            st.error(str(e)); st.code(traceback.format_exc())

with tab2:
    st.subheader("Find your sport (V1 • rules)")
    ans = {}
    for q in INTENT_QUESTIONS:
        ans[q["key"]] = st.selectbox(q["q"], q["choices"], key=f"qa_{q['key']}")
    lang2 = st.selectbox("Language", ["en","ar"], 0, key="q_lang")
    secs2 = st.slider("Seconds per image", 2, 8, 4, key="q_secs")
    voice2 = st.checkbox("Add voice-over", True, key="q_voice")
    bg2 = st.file_uploader("Background music (mp3, optional)", type=["mp3"], key="q_bg")
    use_ai = st.checkbox("Rewrite script with OpenAI (if key present)", value=True)

    if st.button("Recommend & Make Video", type="primary"):
        try:
            profile = build_profile(ans)
            script = build_script(profile, lang=lang2, use_ai=use_ai)
            scenes = extract_scenes(script)
            out = compose_video(scenes, lang=lang2, secs=secs2, voice=voice2, bg_music=bg2)
            data = out.read_bytes()
            st.success(f"Sport: *{profile['sport']}* • Tone: *{profile['tone']}*")
            with st.expander("Script"):
                st.text(script)
            st.video(io.BytesIO(data))
            st.download_button("⬇ Download MP4", data, file_name="final_video.mp4", mime="video/mp4")
            log_event("quiz_video", {"answers": ans, "profile": profile})
        except Exception as e:
            st.error(str(e)); st.code(traceback.format_exc())
