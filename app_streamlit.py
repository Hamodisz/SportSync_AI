# app_streamlit.py
# -- coding: utf-8 --
import time
from typing import List
import streamlit as st
from pathlib import Path
from core.core_engine import run_full_generation, quick_diagnose
from core.backend_gpt import generate_sport_recommendation
from core.user_logger import get_log_stats

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
    try:
        stats = get_log_stats()
        st.markdown("### Log Counters")
        files = stats.get("files", {})
        st.write({"Submissions": files.get("submissions", 0),
                  "Ratings": files.get("ratings", 0),
                  "Chat msgs": files.get("chat", 0),
                  "Events": files.get("events", 0)})
        if "sqlite" in stats:
            st.write({f"DB::{k}": v for k, v in stats["sqlite"].items()})
    except Exception as exc:
        st.warning(f"Logger stats unavailable: {exc}")

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

        st.divider()

# =============== Identity Cards Preview ===============
st.header("Sport Identity Cards")

if "card_ratings" not in st.session_state:
    st.session_state["card_ratings"] = [3, 3, 3]

LIVE_TYPING = st.checkbox("Live typing preview", value=True, key="cards_live_typing")
TYPE_SPEED_MS = st.slider("Typing speed (ms per line)", 1, 40, 8, key="cards_speed")
identity_text = st.text_area("Describe what kind of sport vibe you want", "", height=160)
if st.button("Generate identity cards"):
    with st.spinner("Crafting your identity cards..."):
        answers = {"persona": {"answer": [identity_text]}}
        cards = generate_sport_recommendation(answers, lang)
    headers_ar = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"]
    headers_en = ["🟢 Recommendation #1", "🌿 Recommendation #2", "🔮 Recommendation #3 (Creative)"]
    for i, card_md in enumerate(cards[:3]):
        st.subheader(headers_ar[i] if lang == "ar" else headers_en[i])
        placeholder = st.empty()
        card_md = card_md or ""
        if LIVE_TYPING:
            buffer: List[str] = []
            for line in card_md.splitlines(True):
                buffer.append(line)
                placeholder.markdown("".join(buffer))
                time.sleep(max(TYPE_SPEED_MS, 1) / 1000.0)
        else:
            placeholder.markdown(card_md)
        rating_key = f"card_rating_{i}"
        default_val = st.session_state["card_ratings"][i]
        st.session_state["card_ratings"][i] = st.slider("Rate this card", 1, 5, value=default_val, key=rating_key)
