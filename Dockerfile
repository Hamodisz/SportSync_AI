FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    USE_IMAGE_PLACEHOLDERS=1

WORKDIR /app

# System deps (ffmpeg ضروري للفيديو)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential libglib2.0-0 libsm6 libxrender1 libxext6 \
 && rm -rf /var/lib/apt/lists/*

# لو عندك requirements.txt نستخدمه أولاً
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt || true

# حزم نحتاجها أكيد
RUN pip install moviepy==1.0.3 imageio-ffmpeg==0.4.5 pillow>=10.0.0 gTTS==2.5.1 streamlit==1.35.0 python-dotenv requests

# نسخ بقية المشروع
COPY . /app

# إنشاء مجلدات الإخراج
RUN mkdir -p /app/content_studio/ai_images/outputs \
             /app/content_studio/ai_voice/voices \
             /app/content_studio/ai_video/final_videos

EXPOSE 10000
# Streamlit Web UI
CMD ["bash","-lc","streamlit run app/video_app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
