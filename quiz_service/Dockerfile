FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (FFmpeg لكتابة الفيديو + بعض المكتبات)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# requirements
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

# انسخ كامل المشروع (نحتاج core/ و questions/)
COPY . /app

EXPOSE 10000
CMD ["bash","-lc","streamlit run core/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
