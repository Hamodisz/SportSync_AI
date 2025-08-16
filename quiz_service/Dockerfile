FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# فقط لو بتحتاج ffmpeg لأي صوت/فيديو لاحقاً (ممكن تبقيه)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ثبّت متطلبات خدمة الكويز
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# انسخ كل الكود (بما فيه app/quiz_app.py الموجود عندك)
COPY . /app

EXPOSE 10001
CMD ["bash","-lc","streamlit run app/quiz_app.py --server.port ${PORT:-10001} --server.address 0.0.0.0"]
