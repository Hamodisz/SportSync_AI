# ===== Base =====
FROM python:3.11-slim

# بيئة بايثون أنظف + UTF-8 + ستريمليت بدون واجهة
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# ===== Dependencies (طبقة قابلة للكاش) =====
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --upgrade --no-cache-dir pip setuptools wheel \
 && pip install --no-cache-dir --prefer-binary -r /app/requirements.txt

# ===== App code =====
COPY quiz_service/app.py /app/app.py
COPY core /app/core
COPY analysis /app/analysis
COPY questions /app/questions

# ✅ عرّف المجلدات كـ Packages صريحة لتفادي مشاكل الاستيراد على Render
RUN bash -lc "mkdir -p /app/core /app/analysis && touch /app/core/__init__.py /app/analysis/__init__.py"

# ===== Runtime =====
EXPOSE 10000
# استخدم ${PORT} الذي توفره Render وإلا 10000 افتراضي
CMD ["bash","-lc","streamlit run /app/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
