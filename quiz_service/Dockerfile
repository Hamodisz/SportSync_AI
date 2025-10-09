# ===== Base =====
FROM python:3.11-slim

# بيئة بايثون أنظف (بدون .pyc) + إخراج فوري للّوج
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false

WORKDIR /app

# ===== Dependencies (طبقة قابلة للكاش) =====
COPY quiz_service/requirements.txt /app/requirements.txt
# نحدّث pip/wheel + نصب المتطلبات (prefer-binary لتسريع البناء)
RUN pip install --upgrade --no-cache-dir pip setuptools wheel \
 && pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# ===== App code =====
COPY quiz_service/app.py /app/app.py
COPY core /app/core
COPY analysis /app/analysis
COPY questions /app/questions

# لا نحتاج __init__.py (namespace packages). لو حاب، فعّل السطرين تحت:
# RUN bash -lc "touch /app/core/__init__.py /app/analysis/__init__.py"

# ===== Runtime =====
EXPOSE 10000
# نستخدم bash -lc عشان توسعة ${PORT} تشتغل داخل الحاوية على Render
CMD ["bash","-lc","streamlit run /app/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
