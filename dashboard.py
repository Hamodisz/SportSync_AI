import streamlit as st
from agents.marketing.video_pipeline.full_video_pipeline import generate_ai_video
import os
from datetime import datetime
import uuid

st.set_page_config(page_title="SportSync Dashboard", layout="centered")

# =========================
# ⛳ العنوان الرئيسي
# =========================
st.title("🏁 SportSync AI – Dashboard القيادة الذكية")
st.markdown("مرحبًا 👋 هذا مركز التحكم الكامل لمشروعك، بدون أي كود أو ملفات.")

# =========================
# 🧠 بيانات المستخدم / الفكرة
# =========================
st.subheader("1. أدخل فكرة الفيديو أو بيانات المستخدم:")
user_input = st.text_area("🎯 اكتب الفكرة أو ألصق تحليل المستخدم:", height=150)

# =========================
# 🌐 اختيار اللغة
# =========================
lang = st.selectbox("🌍 اختر اللغة:", ["en", "arabic"])

# =========================
# 📹 نوع الفيديو
# =========================
video_type = st.radio("🎬 نوع الفيديو:", ["🎞 مقطع طويل", "🎯 اقتباس قصير", "📢 إعلان تجريبي"])

# =========================
# 🚀 توليد الفيديو
# =========================
if st.button("🚀 توليد الفيديو الآن"):
    if not user_input or not str(user_input).strip():
        st.warning("الرجاء إدخال الفكرة أو بيانات المستخدم أولاً.")
    else:
        with st.spinner("جاري تحليل البيانات وتوليد الفيديو... ⏳"):
            full_text = user_input if isinstance(user_input, str) else str(user_input)

            user_data = {
                "full_text": full_text,
                "answers": {},
                "video_type": video_type  # ✅ تم الإضافة هنا
            }

            try:
                video_path = generate_ai_video(user_data, lang=lang)
                st.success("✅ تم توليد الفيديو بنجاح!")
                st.video(video_path)
                st.markdown(f"📁 المسار: {video_path}")
            except Exception as e:
                st.error(f"❌ حصل خطأ أثناء التوليد: {e}")

# =========================
# 📈 ملاحظات الأداء
# =========================
with st.expander("📊 ملاحظات أداء وتحليل"):
    st.markdown("""
    - 📈 الأفضل أداءً: فيديوهات بتوقيت 8:00 PM
    - 🧠 نبرة [ثقة + هدوء] كانت الأعلى في التفاعل
    - 🎯 الكلمات المفتاحية الناجحة: inner drive, mental athlete, deep identity
    """)

# =========================
# 🧰 أدوات إضافية (قريبًا)
# =========================
st.sidebar.title("🧰 أدوات قادمة")
st.sidebar.info("🚧 جاري بناء وحدة النشر التلقائي + تدريب الصوت الشخصي")
