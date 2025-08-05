# app/video_app.py

import streamlit as st
import os
from agents.marketing.video_pipeline.generate_ai_video import generate_ai_video

st.set_page_config(page_title="🎬 توليد فيديو AI", layout="centered")
st.title("🎥 توليد فيديو آلي بناءً على شخصيتك")
st.markdown("املأ السمات أدناه وسنقوم بتوليد فيديو يعبر عنك 👇")

# 🧠 إدخال بيانات المستخدم يدوياً
with st.form("user_traits_form"):
    name = st.text_input("👤 اسم المستخدم", value="مستخدم تجريبي")

    energy = st.selectbox("⚡ مستوى الطاقة", ["high", "medium", "low"])
    focus = st.selectbox("🎯 درجة التركيز", ["high", "medium", "low"])
    creativity = st.checkbox("🎨 هل تعتبر نفسك مبدع؟", value=True)

    lang = st.selectbox("🗣 اختر اللغة", ["ar", "en"], index=0)

    submitted = st.form_submit_button("🚀 توليد الفيديو")

if submitted:
    st.info("🔄 جاري توليد الفيديو... يرجى الانتظار")

    # تركيب بيانات المستخدم
    user_data = {
        "name": name,
        "traits": {
            "energy": energy,
            "focus": focus,
            "creative": creativity
        }
    }

    # توليد الفيديو
    video_path = generate_ai_video(user_data, lang)

    if not video_path:
        st.error("❌ فشل توليد الفيديو. تحقق من المدخلات أو حاول لاحقًا.")
    elif not os.path.exists(video_path):
        st.error(f"⚠ الملف لم يتم توليده رغم رجوع هذا المسار:\n`{video_path}`")
    else:
        st.success("✅ تم توليد الفيديو بنجاح!")
        st.video(video_path)
        st.markdown(f"📁 *المسار:* {video_path}")

        with open(video_path, "rb") as file:
            st.download_button("⬇ تحميل الفيديو", file, file_name=os.path.basename(video_path))
