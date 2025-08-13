# app_streamlit.py
import os, streamlit as st, traceback

st.set_page_config(page_title="SportSync", layout="centered")
st.title("✅ SportSync is running on Render")
st.write("PORT:", os.getenv("PORT"))

st.write("Try voice demo:")
from content_studio.ai_voice.voice_generator import generate_voice_from_script

txt = st.text_area("Script", "Hello from Render. This is a quick test.", height=120)
lang = st.selectbox("Lang", ["en", "ar"], index=0)

if st.button("Generate voice"):
    try:
        out = generate_voice_from_script(txt, lang=lang)
        st.audio(out)
        st.success(out)
    except Exception as e:
        st.error(f"Voice error: {e}")
        st.code(traceback.format_exc())
