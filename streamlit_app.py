# streamlit_app.py

import streamlit as st
from content_studio.generate_script.script_generator import generate_script
from content_studio.ai_images.image_generator import generate_images
from content_studio.ai_voice.voice_generator import generate_voice_from_script
from content_studio.ai_video.video_composer import compose_video_from_assets

st.set_page_config(page_title="🎬 فيديو AI شامل", layout="wide")
st.title("🎬 مولّد الفيديوهات الذكية - SportSync AI")

# 📌 إدخالات المستخدم
lang = st.selectbox("اختر اللغة", ["ar", "en"])
quality = st.slider("جودة المحتوى المطلوبة", 1, 10, 5)
tone = st.selectbox("نغمة السكربت", ["عاطفية", "تحفيزية", "تحليلية", "قصصية"])
audience = st.text_input("جمهورك المستهدف (مثال: رياضيين، طلاب...)", "عام")
custom_prompt = st.text_area("🎯 اكتب فكرتك للسكربت (اختياري)", "")

# 📍 زر التشغيل
if st.button("🚀 توليد الفيديو كامل"):
    try:
        with st.spinner("🧠 جاري توليد السكربت..."):
            script = generate_script(
                lang=lang,
                audience=audience,
                quality=quality,
                tone=tone,
                purpose="عام",
                custom_prompt=custom_prompt
            )
            st.success("✅ تم توليد السكربت!")
            st.text_area("📜 السكربت الناتج:", script, height=200)

        with st.spinner("🖼 جاري توليد الصور..."):
            generate_images(script, lang)
            st.success("✅ تم توليد الصور!")

        with st.spinner("🎙 جاري توليد الصوت..."):
            voice_path = generate_voice_from_script(script)
            st.audio(voice_path)
            st.success("✅ تم توليد الصوت!")

        with st.spinner("🎞 جاري تركيب الفيديو..."):
            video_path = compose_video_from_assets()
            st.video(video_path)
            st.success("✅ تم إنتاج الفيديو!")

    except Exception as e:
        st.error(f"❌ خطأ أثناء التشغيل: {e}")
