import streamlit as st
import sys
import os
import pathlib
from pathlib import Path

sys.path.append(str(pathlib.Path().resolve()))

from agents.marketing.video_pipeline.generate_ai_video import generate_ai_video
from content_studio.ai_video.video_composer import compose_video_from_assets
from agents.marketing.video_pipeline.image_generator import generate_images
from agents.marketing.video_pipeline.voice_generator import generate_voiceover

# إعداد الصفحة
st.set_page_config(page_title="🎬 فيديو AI شامل", layout="centered")
st.title("🎥 توليد فيديو AI شامل")
st.markdown("صمّم الفيديو بطريقتك الخاصة 👇")

# 🧠 إدخال البيانات
with st.form("video_form"):
    name = st.text_input("👤 اسم المستخدم", value="مستخدم تجريبي")

    quality = st.selectbox("🎬 درجة جودة الفيديو المطلوبة", [
        "عالية جدًا (احترافي ومؤثر)",
        "متوسطة (واضح وسهل)",
        "خفيفة (سريعة ومباشرة)"
    ])

    audience = st.selectbox("🎯 من هو الجمهور المستهدف؟", [
        "جمهور عام", "رياضيين", "روّاد أعمال", "طلاب", "مدربين", "مبتدئين", "محترفين"
    ])

    creativity = st.checkbox("🎨 هل تريد أن يكون الفيديو إبداعي وغير تقليدي؟", value=True)

    lang = st.selectbox("🗣 اللغة", ["ar", "en"], index=0)

    use_custom_script = st.checkbox("✏ هل تريد كتابة السكربت بنفسك؟", value=False)

    custom_script = ""
    if use_custom_script:
        custom_script = st.text_area("📝 اكتب السكربت الذي تريد تحويله إلى فيديو", height=200)

    uploaded_images = st.file_uploader("🖼 ارفع صورك الخاصة (اختياري)", type=["png", "jpg"], accept_multiple_files=True)

    image_duration = st.slider("⏱ كم مدة عرض كل صورة؟", 1, 10, value=4)

    submit = st.form_submit_button("🚀 توليد الفيديو")

# 🎬 عند الضغط على "توليد الفيديو"
if submit:
    st.info("🛠 جاري التحضير...")

    IMAGES_DIR = Path("content_studio/ai_images/outputs/")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for file in IMAGES_DIR.glob("*"):
        file.unlink()

    VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")

    user_data = {
        "name": name,
        "traits": {
            "quality": quality,
            "audience": audience,
            "creative": creativity
        }
    }

    script = ""

    if use_custom_script and custom_script.strip():
        script = custom_script.strip()
        generate_images(script, lang)
        generate_voiceover(script, lang)
    else:
        video_path = generate_ai_video(user_data, lang)
        if not video_path:
            st.error("❌ فشل توليد الفيديو.")
            st.stop()
        script = "..."  # placeholder

    if uploaded_images:
        for i, file in enumerate(uploaded_images):
            img_path = IMAGES_DIR / f"user_image_{i+1}.png"
            with open(img_path, "wb") as f:
                f.write(file.read())

    # عرض الصور
    image_files = sorted(IMAGES_DIR.glob("*"))
    if image_files:
        st.subheader("📷 الصور المستخدمة:")
        st.image([str(p) for p in image_files], width=250)

    # عرض الصوت
    if VOICE_PATH.exists():
        st.subheader("🎙 الصوت المولد:")
        st.audio(str(VOICE_PATH))

    # توليد الفيديو
    st.info("🎞 جاري تركيب الفيديو النهائي...")
    video_path = compose_video_from_assets(image_duration=image_duration)

    if not video_path or not os.path.exists(video_path):
        st.error("❌ فشل تركيب الفيديو.")
    else:
        st.success("✅ تم توليد الفيديو بنجاح!")
        st.video(video_path)

        with open(video_path, "rb") as f:
            st.download_button("⬇ تحميل الفيديو", f, file_name=os.path.basename(video_path))
