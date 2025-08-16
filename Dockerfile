FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    USE_IMAGE_PLACEHOLDERS=1 \
    START_PATH="app/video_app.py"

WORKDIR /app

# System deps (ffmpeg ضروري للفيديو)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# App code
COPY . /app

# Ensure output dirs exist
RUN mkdir -p /app/content_studio/ai_images/outputs \
             /app/content_studio/ai_voice/voices \
             /app/content_studio/ai_video/final_videos

EXPOSE 10000

# يقرأ أي ملف ستريمليت من متغير START_PATH
CMD ["bash","-lc","streamlit run ${START_PATH} --server.port ${PORT:-10000} --server.address 0.0.0.0"]
