"""
SportSync AI - Minimal FastAPI Backend for Vercel
Ultra-simple version that MUST work
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import json

# Create FastAPI app
app = FastAPI(title="SportSync AI", version="2.3")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    return {
        "status": "success",
        "message": "SportSync AI API is running!",
        "version": "2.3",
        "endpoints": {
            "/api/health": "Health check",
            "/api/simple-recommend": "Get recommendations"
        }
    }

# Health endpoint
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "version": "2.3"
    }

# Simple recommend endpoint
@app.post("/api/simple-recommend")
async def simple_recommend(request: dict):
    """Generate sport recommendations"""
    try:
        answers = request.get("answers", [])
        language = request.get("language", "ar")

        # Analyze answers
        answers_text = " ".join([str(a.get("answer_text", "")).lower() for a in answers])

        # Arabic recommendations
        if language == "ar":
            # Calm/Focus keywords
            if any(word in answers_text for word in ["هادئ", "تركيز", "استرخاء"]):
                recs = [
                    "🧘 اليوغا التأملية - رياضة ذهنية-جسدية تناسب طبيعتك الهادئة",
                    "🎯 الرماية بالقوس - تركيز ودقة وسكون داخلي",
                    "🌲 المشي التأملي - انغماس كامل في الطبيعة"
                ]
            # Active/Adrenaline keywords
            elif any(word in answers_text for word in ["أدرينالين", "سريع", "حركة"]):
                recs = [
                    "🏃 Parkour - حركة حرة وأدرينالين نقي",
                    "🚴 ركوب الدراجات الجبلية - سرعة ومغامرة",
                    "🧗 تسلق الصخور - تحدي الجاذبية!"
                ]
            # Balanced
            else:
                recs = [
                    "⚽ كرة القدم الصغيرة - مزيج من المتعة والعمل الجماعي",
                    "🏊 السباحة - رياضة متكاملة هادئة ونشطة",
                    "🎾 التنس - تحدي ذهني وجسدي معاً"
                ]
        else:
            # English
            recs = [
                "🧘 Yoga - Mind-body balance",
                "🏃 Parkour - Dynamic movement",
                "⚽ Futsal - Balanced team sport"
            ]

        return {
            "success": True,
            "recommendations": recs,
            "message": "API working perfectly!"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Something went wrong"
        }

# Required for Vercel - don't remove this comment
# The 'app' variable is the ASGI application
