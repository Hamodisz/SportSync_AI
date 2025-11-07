# 🚀 SportSync AI - الباك إند (FastAPI)

## نظرة عامة
API backend بسيط يربط واجهة React بنماذج OpenAI الثلاثة.

## المميزات
- ⚡ **Fast**: GPT-3.5 للتحليل السريع
- 🧠 **Reasoning**: o1-mini لتحليل Z-layer
- 🎯 **Intelligence**: GPT-4 للتوصية النهائية
- 🔐 **آمن**: API keys في .env
- ⚙️ **CORS**: يدعم React frontend

## التثبيت

```bash
# 1. انتقل للمجلد
cd api

# 2. إنشاء بيئة افتراضية
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. تثبيت المكتبات
pip install -r requirements.txt

# 4. إعداد المتغيرات البيئية
cp ../.env .env
# تأكد أن OPENAI_API_KEY موجود في .env
```

## التشغيل

```bash
# تشغيل السيرفر
python backend_simple.py

# أو باستخدام uvicorn مباشرة
uvicorn backend_simple:app --reload --port 8000
```

السيرفر سيعمل على: `http://localhost:8000`

## الـ Endpoints

### 1. POST /api/analyze
تحليل رسالة المستخدم بنظام الذكاء الثلاثي.

**Request:**
```json
{
  "message": "حاسس بضغط كبير ومافي وقت"
}
```

**Response:**
```json
{
  "recommendation": "التوصية النهائية بالعربية...",
  "layers": {
    "fast": 2.1,
    "reasoning": 8.3,
    "intelligence": 4.2
  },
  "total_time": 14.6
}
```

### 2. GET /health
فحص حالة السيرفر والنماذج.

**Response:**
```json
{
  "status": "healthy",
  "models": ["gpt-3.5-turbo", "o1-mini", "gpt-4"]
}
```

## الاختبار

```bash
# اختبار health check
curl http://localhost:8000/health

# اختبار التحليل
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "حاسس بضغط كبير"}'
```

## ربط React Frontend

في ملف React (`SportFinderPro.jsx`), غيّر الـ API endpoint:

```javascript
// بدلاً من:
const response = await fetch('https://api.openai.com/v1/chat/completions', ...)

// استخدم:
const response = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: userMessage })
});
```

## النشر (Production)

### Render.com
```yaml
# render.yaml
services:
  - type: web
    name: sportsync-api
    env: python
    buildCommand: "pip install -r api/requirements.txt"
    startCommand: "cd api && uvicorn backend_simple:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: OPENAI_API_KEY
        sync: false
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt .
RUN pip install -r requirements.txt
COPY api/ .
CMD ["uvicorn", "backend_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

## الأمان

⚠️ **مهم:**
- لا ترفع `.env` أبداً
- استخدم HTTPS في production
- أضف rate limiting للـ API
- راقب استخدام OpenAI API

## استكشاف الأخطاء

### خطأ: "API key invalid"
```bash
# تحقق من .env
cat .env | grep OPENAI_API_KEY
```

### خطأ: "CORS error"
تأكد أن `allow_origins` في الكود يطابق عنوان React:
```python
allow_origins=["http://localhost:3000"]
```

### خطأ: "Model not found"
بعض الحسابات لا تدعم o1-mini. غيّره إلى:
```python
model="gpt-4"  # بدلاً من o1-mini
```

---

Made with 🧠 by SportSync AI Team
