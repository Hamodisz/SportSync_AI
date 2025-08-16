FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# (بسيطة وخفيفة – ما فيها ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# باكجات بايثون
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# انسخ كل الريبو عشان core/app.py يكون موجود
COPY . /app

EXPOSE 10000

# شغّل ستريملت على ملف الأسئلة الموجود عندك
CMD ["bash","-lc","streamlit run core/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
