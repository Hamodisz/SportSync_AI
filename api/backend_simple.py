"""
Fast API Backend for SportSync AI
Connects React frontend with OpenAI models
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SportSync AI API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

class UserMessage(BaseModel):
    message: str

class AIResponse(BaseModel):
    recommendation: str
    layers: dict
    total_time: float

@app.post("/api/analyze", response_model=AIResponse)
async def analyze_user(user_input: UserMessage):
    """
    Analyzes user input using 3-layer AI system:
    1. Fast (GPT-3.5) - Quick insights
    2. Reasoning (o1-mini) - Deep Z-layer
    3. Intelligence (GPT-4) - Final recommendation
    """
    import time
    start_total = time.time()
    
    try:
        # Layer 1: Fast Analysis
        fast_start = time.time()
        fast_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """استخرج من رسالة المستخدم:
1. emotion: الحالة العاطفية
2. constraints: القيود العملية
3. goals: الأهداف الحقيقية
4. readiness_level: مستوى الجاهزية

أجب بـ JSON فقط."""
                },
                {"role": "user", "content": user_input.message}
            ],
            temperature=0.3,
            max_tokens=400
        )
        fast_time = time.time() - fast_start
        quick_insights = fast_response.choices[0].message.content
        
        # Layer 2: Deep Reasoning
        reasoning_start = time.time()
        reasoning_response = openai.ChatCompletion.create(
            model="o1-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""المستخدم قال: "{user_input.message}"

التحليل السريع: {quick_insights}

حلل Z-layer (الدوافع الخفية):
1. الدوافع الحقيقية
2. الحواجز النفسية
3. مستوى الاستعداد
4. الرياضة المثالية

اكتب تحليل عميق بالعربية."""
                }
            ],
            temperature=1,
            max_tokens=2000
        )
        reasoning_time = time.time() - reasoning_start
        deep_analysis = reasoning_response.choices[0].message.content
        
        # Layer 3: Final Intelligence
        intelligence_start = time.time()
        intelligence_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"""أنت مستشار رياضي محترف.

التحليل السريع: {quick_insights}
التحليل العميق: {deep_analysis}

اكتب توصية user-friendly بالعربية:
- استخدم "أنت" مباشرة
- كأنك صديق يساعد صديقه
- بدون bullet points
- فقرات طبيعية"""
                },
                {"role": "user", "content": "اكتب التوصية النهائية"}
            ],
            temperature=0.8,
            max_tokens=1500
        )
        intelligence_time = time.time() - intelligence_start
        final_recommendation = intelligence_response.choices[0].message.content
        
        total_time = time.time() - start_total
        
        return AIResponse(
            recommendation=final_recommendation,
            layers={
                "fast": fast_time,
                "reasoning": reasoning_time,
                "intelligence": intelligence_time
            },
            total_time=total_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models": ["gpt-3.5-turbo", "o1-mini", "gpt-4"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
