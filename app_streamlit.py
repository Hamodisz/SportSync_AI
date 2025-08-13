# app_streamlit.py
# coding: utf-8
import os, json
import streamlit as st
from pathlib import Path

from core.core_engine import run_full_generation, quick_diagnose

# إعداد الصفحة
st.set_page_config(page_title="SportSync — Quick Video", layout="centered")
st.title("SportSync — Video + Personalizer (V1.1)")

# خيارات بسيطة
lang = st.selectbox("Language", ["en", "ar"], index=0)

DEFAULT_SCRIPT = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""
script = st.text_area("Script", value=DEFAULT_SCRIPT, height=220)
secs = st.slider("Seconds per image", 2, 8, 4, 1)
add_voice = st.checkbox("Add voice-over", value=False)
use_ai = st.checkbox("Use AI images (OpenAI)", value=True)
show_debug = st.checkbox("Show debug (diagnose)", value=True)

col1, col2 = st.columns(2)

with col1:
    if st.button("Generate video", use_container_width=True):
        try:
            with st.spinner("Generating images / voice / video..."):
                res = run_full_generation(
                    user_data={"topic":"sports motivation","traits":{"tone":"emotional"}},
                    lang=lang,
                    image_duration=secs,
                    override_script=script,
                    mute_if_no_voice=not add_voice,
                    skip_cleanup=False,   # ننظّف صور قديمة قبل كل تشغيل
                    use_ai_flag=use_ai,
                )

            if res.get("error"):
                st.error(f"ERROR: {res['error']}")
                if show_debug:
                    st.code(json.dumps(quick_diagnose(), ensure_ascii=False, indent=2), language="json")
            else:
                st.success("✅ Video ready!")
                # عرض الصور الناتجة
                st.write("Images:")
                for p in res["images"]:
                    if Path(p).exists():
                        st.image(p, width=512)

                # عرض الفيديو كـ bytes لإزالة مشاكل المسارات
                vp = res["video"]
                if vp and Path(vp).exists():
                    with open(vp, "rb") as f:
                        st.video(f.read())
                    st.download_button("Download MP4", data=open(vp, "rb").read(),
                                       file_name="final_video.mp4", mime="video/mp4")
                    st.write(f"Video path: {vp}")
                else:
                    st.warning("Video file not found after compose. Check logs.")

                if show_debug:
                    st.code(json.dumps(quick_diagnose(), ensure_ascii=False, indent=2), language="json")

        except Exception as e:
            st.error(f"Exception: {e}")
            if show_debug:
                st.exception(e)

with col2:
    if st.button("Quick diagnose", use_container_width=True):
        st.code(json.dumps(quick_diagnose(), ensure_ascii=False, indent=2), language="json")
