from pathlib import Path
import streamlit as st

VID_DIR = Path("content_studio/ai_video/final_videos")
st.set_page_config(page_title="Preview Videos", layout="wide")
st.title("🎞 Final Videos")

files = sorted(VID_DIR.glob("*.mp4"))
if not files:
    st.warning("لا توجد ملفات MP4 داخل " + str(VID_DIR.resolve()))
else:
    for p in files:
        st.subheader(p.name)
        st.video(str(p))
