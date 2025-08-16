FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ننسخ المتطلبات من نفس الـ Root (quiz_service)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ننسخ بقية السورس
COPY . /app

EXPOSE 10001
CMD ["bash","-lc","streamlit run quiz_app.py --server.port ${PORT:-10000} --server.address 0.0.0.0"]
