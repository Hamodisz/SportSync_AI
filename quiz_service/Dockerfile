FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# متطلبات
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# كود التطبيق
COPY quiz_service/app.py /app/app.py
COPY core /app/core
COPY analysis /app/analysis
COPY questions /app/questions

# عرّف المجلدات كباكج بدون Heredoc
RUN bash -lc "mkdir -p /app/core /app/analysis && touch /app/core/_init.py /app/analysis/init_.py"

EXPOSE 10000
CMD ["bash","-lc","streamlit run /app/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
