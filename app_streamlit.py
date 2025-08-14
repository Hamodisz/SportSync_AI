# app_streamlit.py
# واجهة بسيطة تولّد صور/صوت/فيديو وتعرض النتيجة مع زر تنزيل

from pathlib import Path
import os
import json
import streamlit as st

# استيراد المحرك
from core.core_engine import run_full_generation, quick_diagnose

st.set_page_config(page_title="SportSync — Quick Video", layout="centered")

st.title("SportSync — Video + Personalizer (V1.1)")

# -------- الإعدادات --------
lang = st.selectbox("Language", ["en", "ar"], index=0)

DEFAULT_SCRIPT = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""

script = st.text_area("Script", DEFAULT_SCRIPT, height=220)

secs = st.slider("Seconds per image", 2, 8, 4)

col1, col2 = st.columns(2)
with col1:
    add_voice = st.checkbox("Add voice-over", value=False)
with col2:
    show_debug = st.checkbox("Show debug (diagnose)", value=True)

# اختيارات توليد الصور (بيئة/متغيرات بدون تغيير توقيع الدوال)
use_openai = st.checkbox("Use AI images (OpenAI)", value=False)
use_stock  = st.checkbox("Use stock photos (free)", value=True)

st.divider()

# -------- أزرار --------
c1, c2 = st.columns(2)

def show_diag():
    d = quick_diagnose()
    st.code(json.dumps(d, ensure_ascii=False, indent=2), language="json")

with c2:
    if st.button("Quick diagnose"):
        show_diag()

# -------- تنفيذ --------
with c1:
    if st.button("Generate video", use_container_width=True):
        # تمرير التفضيلات عبر متغيرات بيئية (تتقرأ داخل generate_images)
        os.environ["USE_OPENAI_IMAGES"] = "1" if use_openai else "0"
        os.environ["USE_STOCK_IMAGES"]  = "1" if use_stock else "0"

        with st.status("Generating images / voice / video...", expanded=True) as s:
            # user_data بسيط
            user_data = {"topic": "sports motivation", "traits": {"tone": "emotional"}}

            res = run_full_generation(
                user_data=user_data,
                lang=lang,
                image_duration=int(secs),
                override_script=script,
                mute_if_no_voice=not add_voice,
                skip_cleanup=False,
            )

            if res.get("error"):
                st.error(f"ERROR: {res['error']}")
                if show_debug:
                    show_diag()
                s.update(label="Failed", state="error")
            else:
                # عرض الصور المصنوعة (إن وجدت)
                images = sorted([str(p) for p in Path("content_studio/ai_images/outputs").glob("*")])
                if images:
                    st.caption("Images used:")
                    st.image(images, use_column_width=True)

                # عرض الفيديو + زر تنزيل
                video_path = res.get("video")
                if video_path and Path(video_path).exists():
                    st.success("Video is ready 🎉")
                    st.video(str(video_path))

                    # زر تنزيل
                    vb = Path(video_path).read_bytes()
                    st.download_button(
                        "Download MP4",
                        data=vb,
                        file_name=Path(video_path).name,
                        mime="video/mp4",
                        use_container_width=True,
                    )
                else:
                    st.warning("Video file not found after generation.")

                if add_voice and res.get("voice"):
                    st.caption(f"Voice: {res['voice']}")

                if show_debug:
                    show_diag()

                s.update(label="Done", state="complete")
