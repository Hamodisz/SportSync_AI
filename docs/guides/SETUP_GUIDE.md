# 🚀 SportSync AI - Complete Setup Guide

## Phase 2: Collaborative Filtering & API Integration

---

## 📦 What's New?

### ✨ Features Added:
1. **Supabase Database Integration** - قاعدة بيانات متقدمة
2. **Collaborative Filtering Engine** - توصيات تعاونية ذكية
3. **FastAPI RESTful API** - واجهة برمجية كاملة
4. **User Analytics & Tracking** - تتبع وتحليلات المستخدمين
5. **Hybrid Recommendations** - دمج CF + Content-Based

---

## 🔧 Installation

### 1. Clone & Setup
```bash
git clone https://github.com/Hamodisz/SportSync_AI.git
cd SportSync_AI
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

#### Required Variables:
```bash
# OpenAI API (for dual-model AI)
OPENAI_API_KEY=sk-your-key-here
CHAT_MODEL_DISCOVERY=o4-mini
CHAT_MODEL_REASONING=gpt-5

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

---

## 🗄️ Database Setup (Supabase)

### Option 1: Supabase Cloud (Recommended)

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Copy URL and API keys

2. **Run SQL Schema**
   ```bash
   # In Supabase SQL Editor, run:
   database/schema.sql
   ```

3. **Configure Environment**
   ```bash
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGc...  # anon key
   SUPABASE_SERVICE_KEY=eyJhbGc...  # service_role key
   ```

### Option 2: Self-Hosted Supabase

```bash
# Using Docker
git clone https://github.com/supabase/supabase
cd supabase/docker
cp .env.example .env
docker-compose up -d

# Then run schema
psql -h localhost -U postgres -d postgres -f database/schema.sql
```

---

## 🏃 Running the System

### Option 1: Streamlit App (UI)
```bash
streamlit run app_streamlit.py
```
Access: `http://localhost:8501`

### Option 2: FastAPI Server (API)
```bash
# Start API server
cd api
python main.py

# Or with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
Access: `http://localhost:8000/docs` (Swagger UI)

### Option 3: Both (Recommended for Production)
```bash
# Terminal 1: API Server
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit UI
streamlit run app_streamlit.py
```

---

## 🔌 API Endpoints

### Base URL: `http://localhost:8000`

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "services": {
    "database": "connected",
    "cf_engine": "ready",
    "users_in_cf": 150,
    "sports_in_cf": 45
  }
}
```

### 2. Submit Quiz
```bash
POST /api/v1/quiz/submit
```

**Request Body:**
```json
{
  "user_identifier": "user@example.com",
  "language": "ar",
  "answers": [
    {
      "question_id": "1",
      "question_text": "كيف تشعر عادة عند مواجهة تحدي جديد؟",
      "answer": "متحمس جداً",
      "category": "risk_tolerance"
    }
  ],
  "identity_scores": {
    "warrior": 7.5,
    "explorer": 8.2
  },
  "trait_scores": {
    "extroversion": 6.5,
    "competitiveness": 8.0
  }
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "user_id": "uuid-here",
  "recommendations": [
    {
      "sport_label": "كرة القدم",
      "match_percentage": 92,
      "predicted_rating": 4.5,
      "confidence": 0.85,
      "hybrid_score": 4.3
    }
  ],
  "cf_enabled": true,
  "hybrid_mode": true
}
```

### 3. Submit Rating
```bash
POST /api/v1/rating/submit
```

**Request Body:**
```json
{
  "user_identifier": "user@example.com",
  "sport_label": "كرة القدم",
  "rating": 4.5,
  "was_recommended": true,
  "was_clicked": true,
  "was_liked": true
}
```

### 4. Get Recommendations
```bash
GET /api/v1/recommendations/{user_identifier}?n=10
```

### 5. Get Similar Users
```bash
GET /api/v1/similar-users/{user_identifier}?top_k=10
```

### 6. Popular Sports
```bash
GET /api/v1/analytics/popular-sports?limit=20
```

---

## 🧠 How Collaborative Filtering Works

### Architecture Flow:

```
[User Completes Quiz]
        ↓
[Discovery Model (o4-mini)]
   Quick Pattern Analysis
        ↓
[Reasoning Model (gpt-5)]
   Deep Recommendations
        ↓
[Collaborative Filtering]
   ├─ Find Similar Users
   ├─ Aggregate Their Preferences
   └─ Hybrid Score Calculation
        ↓
[Final Recommendations]
   (Content-Based + CF)
```

### Hybrid Score Formula:
```python
hybrid_score = (0.6 × content_based_score) + (0.4 × cf_score)
```

---

## 📊 Database Schema

### Main Tables:
- `users` - User profiles
- `quiz_responses` - Quiz answers
- `user_traits` - Psychological profiles
- `recommendations` - Generated recommendations
- `sport_ratings` - User ratings (for CF)
- `similar_users` - Precomputed similarities
- `analytics_events` - User activity tracking

---

## 🔒 Security & Privacy

- ✅ Anonymous user identifiers (hashed)
- ✅ Row Level Security (RLS) enabled
- ✅ No personal data storage
- ✅ Encrypted connections
- ✅ CORS configured for production

---

## 📈 Performance Optimization

### Collaborative Filtering:
- **Precomputed Similarities**: Updated periodically
- **Matrix Factorization**: Optional for large scale
- **Caching**: Redis integration (optional)

### API Performance:
- **Background Tasks**: Quiz data saved asynchronously
- **Connection Pooling**: Database connections managed
- **Rate Limiting**: Built-in protection

---

## 🧪 Testing

### Test API Endpoints:
```bash
# Health check
curl http://localhost:8000/health

# Submit test quiz
curl -X POST http://localhost:8000/api/v1/quiz/submit \
  -H "Content-Type: application/json" \
  -d @test_data/sample_quiz.json

# Get recommendations
curl http://localhost:8000/api/v1/recommendations/test@example.com
```

### Test Streamlit UI:
```bash
streamlit run app_streamlit.py
# Navigate to Quiz tab
# Submit answers
# Check recommendations
```

---

## 🚀 Deployment

### Render.com (Recommended)

1. **Create Web Service**
   - Repository: Your GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   - Add all variables from `.env`
   - Supabase credentials
   - OpenAI API key

3. **Streamlit (Separate Service)**
   - Start Command: `streamlit run app_streamlit.py --server.port $PORT`

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# API
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📝 Configuration

### Collaborative Filtering Settings:
```python
# In ml/collaborative_filtering.py

MIN_RATINGS = 5  # Minimum ratings per user
TOP_K_SIMILAR = 20  # Number of similar users
CF_WEIGHT = 0.4  # Weight in hybrid (0.0 - 1.0)
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score
```

### API Settings:
```python
# In api/main.py

CORS_ORIGINS = ["*"]  # Configure for production
API_VERSION = "2.0.0"
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📞 Support

- GitHub Issues: [Report bugs](https://github.com/Hamodisz/SportSync_AI/issues)
- Documentation: [Full docs](https://github.com/Hamodisz/SportSync_AI/tree/main/docs)

---

## 🎯 Roadmap

- [x] Phase 1: Dual-Model AI System
- [x] Phase 2: Collaborative Filtering + API
- [ ] Phase 3: Advanced ML Models (Matrix Factorization)
- [ ] Phase 4: Real-time Recommendations
- [ ] Phase 5: Mobile App Integration

---

**Built with ❤️ for helping people discover their perfect sport**
