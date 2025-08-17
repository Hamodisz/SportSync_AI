FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# اختياري: لو احتجته لاحقاً
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# متطلبات خدمة الكويز
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# انسخ كل الريبو عشان core/ و analysis/ و questions/ تكون موجودة
COPY . /app

EXPOSE 10000
CMD bash -lc 'set -e; \
  TARGET=""; \
  if [ -f "quiz_service/app.py" ]; then TARGET="quiz_service/app.py"; \
  elif [ -f "app/quiz_app.py" ]; then TARGET="app/quiz_app.py"; \
  elif [ -f "core/app.py" ]; then TARGET="core/app.py"; \
  else echo "❌ لم أجد ملف واجهة الـ Quiz (quiz_service/app.py أو app/quiz_app.py أو core/app.py)"; ls -la; exit 1; fi; \
  streamlit run "$TARGET" --server.port ${PORT:-10000} --server.address 0.0.0.0'
