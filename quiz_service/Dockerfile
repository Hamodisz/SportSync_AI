# Quiz Service Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# متطلبات
COPY quiz_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# نسخ الكود
COPY quiz_service/app.py /app/app.py
COPY core /app/core
COPY analysis /app/analysis
COPY questions /app/questions

# تأكد أن المجلدات تعتبر باكيج (لو نسيت _init_.py)
RUN python - <<'PY'\n\
import pathlib\n\
for d in ('/app/core','/app/analysis'):\n\
    p=pathlib.Path(d)/'_init_.py'\n\
    p.exists() or p.write_text('# package marker\\n', encoding='utf-8')\n\
print('packages ready')\n\
PY

EXPOSE 10000
CMD ["bash","-lc","streamlit run app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
