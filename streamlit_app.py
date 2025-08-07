# streamlit_app.py

import streamlit as st
import sys
import pathlib
from pathlib import Path
import os

# ✅ دعم المسارات الداخلية للمشروع (agents, content_studio...)
sys.path.append(str(pathlib.Path().resolve()))

from agents.marketing.video_pipeline.generate_ai_video import generate_ai_video
from content_studio.ai_video.video_composer import compose_video_from_assets
from agents.marketing.video_pipeline.image_generator import generate_images
from agents.marketing.video_pipeline.voice_generator import generate_voiceover

# إعداد الصفحة
st.set_page_config(page_title="🎬 فيديو AI شامل", layout="centered")
st.title("🎥 توليد فيديو باستخدام الذكاء الاصطناعي")
st.markdown("أنشئ فيديو خاص بناءً على شخصيتك أو نصك 👇")

# 🧠 إدخال البيانات
with st.form("video_form"):
    name = st.text_input("👤 اسم المستخدم", value="مستخدم تجريبي")

    # 🌟 خيارات مفهومة أكثر
    energy = st.selectbox("⚡ مستوى الطاقة العام", ["مرتفعة", "متوسطة", "منخفضة"])
    focus = st.selectbox("🎯 درجة التركيز", ["عالٍ", "متوسط", "منخفض"])
    creativity = st.radio("🎨 هل تعتبر نفسك شخصًا مبدعًا؟", ["نعم", "لا"], index=0) == "نعم"

    lang = st.selectbox("🌐 اختر اللغة", ["ar", "en"], index=0)

    quality = st.select_slider("🎞 جودة المحتوى المطلوبة", options=["عادية", "جيدة", "احترافية"], value="جيدة")
    audience = st.text_input("🎯 الجمهور المستهدف (مثال: رياضيين، طلاب...)", value="عام")

    use_custom_script = st.checkbox("✏ أريد كتابة السكربت بنفسي")
    custom_script = ""
    if use_custom_script:
        custom_script = st.text_area("📝 أدخل السكربت النصي هنا")

    uploaded_images = st.file_uploader("📸 ارفع صورك الخاصة (اختياري)", type=["png", "jpg"], accept_multiple_files=True)

    image_duration = st.slider("⏱ مدة عرض كل صورة (بالثواني)", 1, 10, value=4)

    submit = st.form_submit_button("🚀 توليد الفيديو")

# ✅ عند الضغط على توليد الفيديو
if submit:
    st.info("🚧 جاري تجهيز كل شيء...")

    # 1. تنظيف مجلد الصور
    IMAGES_DIR = Path("content_studio/ai_images/outputs/")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for f in IMAGES_DIR.glob("*"):
        f.unlink()

    # 2. مسار الصوت
    VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")

    # 3. تجهيز البيانات
    user_data = {
        "name": name,
        "traits": {
            "energy": energy,
            "focus": focus,
            "creative": creativity,
            "quality": quality,
            "audience": audience
        }
    }

    script = ""

    # 4. إذا المستخدم كتب سكربت بنفسه
    if use_custom_script and custom_script.strip():
        script = custom_script.strip()
        generate_images(script, lang)
        generate_voiceover(script, lang)
    else:
        video_path = generate_ai_video(user_data, lang)
        if not video_path:
            st.error("❌ فشل في توليد الفيديو.")
            st.stop()
        script = "..."  # مجرد placeholder

    # 5. معالجة الصور المرفوعة
    if uploaded_images:
        for i, file in enumerate(uploaded_images):
            img_path = IMAGES_DIR / f"user_image_{i+1}.png"
            with open(img_path, "wb") as f:
                f.write(file.read())

    # 6. عرض الصور
    image_files = sorted(IMAGES_DIR.glob("*.png"))
    if image_files:
        st.subheader("📷 الصور المستخدمة:")
        st.image([str(p) for p in image_files], width=250)

    # 7. عرض الصوت
    if VOICE_PATH.exists():
        st.subheader("🎙 الصوت الناتج:")
        st.audio(str(VOICE_PATH))

    # 8. توليد الفيديو النهائي
    st.info("🎞 جاري تركيب الفيديو النهائي...")
    video_path = compose_video_from_assets(image_duration=image_duration)

    if not video_path or not os.path.exists(video_path):
        st.error("❌ فشل تركيب الفيديو.")
    else:
        st.success("✅ تم توليد الفيديو بنجاح!")
        st.video(video_path)
        with open(video_path, "rb") as f:
            st.download_button("⬇ تحميل الفيديو", f, file_name=os.path.basename(video_path))
