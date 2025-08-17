FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# (اختياري) ffmpeg مو ضروري للـ Quiz، بس نخليه لو احتجته لاحقاً
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# باكجات البايثون
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# نسخ التطبيق + الديبندنسي من جذر الريبو
COPY quiz_service/app.py /app/app.py
COPY core /app/core
COPY analysis /app/analysis
COPY questions /app/questions

EXPOSE 10000
CMD ["bash","-lc","streamlit run app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
