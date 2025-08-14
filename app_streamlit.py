# app_streamlit.py
# -- coding: utf-8 --
import streamlit as st
from pathlib import Path
from core.core_engine import run_full_generation, quick_diagnose

st.set_page_config(page_title="SportSync — Quick Video", layout="centered")

st.title("SportSync — Video + Personalizer (V1.1)")

lang = st.selectbox("Language", ["en","ar"], index=0)

DEFAULT_SCRIPT = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""

script = st.text_area("Script", DEFAULT_SCRIPT, height=240)
seconds = st.slider("Seconds per image", 2, 8, 4)
add_voice = st.checkbox("Add voice-over", value=False)
show_diag = st.checkbox("Show debug (diagnose)", value=True)

col1, col2 = st.columns([1,1])
gen_btn = col1.button("Generate video", type="primary")
diag_btn = col2.button("Quick diagnose")

if diag_btn:
    st.json(quick_diagnose())

if gen_btn:
    with st.spinner("Generating images / voice / video..."):
        result = run_full_generation({
            "script": script,
            "lang": lang,
            "seconds_per_image": seconds,
            "add_voice": add_voice
        })

    if not result.get("ok"):
        st.error(f"ERROR: {result.get('error','unknown')}")
        if show_diag:
            st.json(result.get("debug", {}))
    else:
        st.success("✅ Done.")
        if show_diag:
            st.json({
                "images": result["images"],
                "voice": result["voice"],
                "video": result["video"]
            })

        # أعرض الفيديو فعليًا من الملف (بايتس)
        vpath = Path(result["video"])
        if vpath.exists():
            with open(vpath, "rb") as f:
                st.video(f.read())
            st.download_button("Download MP4", data=open(vpath, "rb").read(), file_name="final_video.mp4")
        else:
            st.warning("Video file not found after pipeline.")
