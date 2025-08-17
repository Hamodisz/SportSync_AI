# quiz_service/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# أدوات النظام (streamlit + pillow + moviepy يعتمدون على libjpeg/zlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# متطلبات الخدمة
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# ننسخ الأكواد المطلوبة من جذر الريبو (بسبب Build Context = ".")
COPY core /app/core
COPY analysis /app/analysis
COPY questions /app/questions
COPY quiz_service/app.py /app/app.py

EXPOSE 10000
CMD ["bash","-lc","streamlit run /app/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
