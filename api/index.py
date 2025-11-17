# api/index.py
"""
SportSync AI - FastAPI Backend for Vercel
This is the main API endpoint that Vercel will deploy
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our core logic
try:
    from src.core.backend_gpt import generate_sport_recommendation
    from src.analysis.layer_z_engine import calculate_z_scores_from_questions
except Exception as e:
    print(f"Import error: {e}")
    # Fallback imports will be handled

# Create FastAPI app
app = FastAPI(
    title="SportSync AI API",
    description="AI-powered sport recommendation system",
    version="2.2"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class Answer(BaseModel):
    question_key: str
    answer_text: str

class RecommendationRequest(BaseModel):
    answers: List[Answer]
    language: str = "ar"
    user_id: Optional[str] = None

class RecommendationResponse(BaseModel):
    success: bool
    recommendations: List[str]
    analysis_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Health check endpoint
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "SportSync AI API",
        "version": "2.2",
        "endpoints": {
            "/": "Health check",
            "/api/recommend": "POST - Get sport recommendations",
            "/api/questions": "GET - Get questions list",
            "/api/sports": "GET - Get available sports"
        }
    }

@app.get("/api/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "version": "2.2"
    }

@app.post("/api/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Generate sport recommendations based on user answers

    This endpoint:
    1. Receives user answers to questions
    2. Analyzes personality using Layer-Z and 15 systems
    3. Generates 3 personalized sport recommendations
    """
    try:
        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Add OPENAI_API_KEY to Vercel environment variables."
            )

        # Convert answers to format expected by backend
        answers_dict = {}
        for answer in request.answers:
            answers_dict[answer.question_key] = {
                "answer": answer.answer_text
            }

        # Generate recommendations
        try:
            recommendations = generate_sport_recommendation(
                answers=answers_dict,
                lang=request.language
            )

            return RecommendationResponse(
                success=True,
                recommendations=recommendations,
                analysis_summary={
                    "total_questions": len(request.answers),
                    "language": request.language,
                    "user_id": request.user_id
                }
            )
        except Exception as e:
            # If main function fails, return a helpful error
            return RecommendationResponse(
                success=False,
                recommendations=[],
                error=f"Analysis failed: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions")
async def get_questions(lang: str = "ar"):
    """Get the list of questions for the specified language"""
    import json

    try:
        # Load questions from data folder
        questions_file = f"data/questions/arabic_questions_v2.json" if lang == "ar" else "data/questions/english_questions_v2.json"

        # Fallback to sample if main file not found
        if not Path(questions_file).exists():
            questions_file = f"data/questions/arabic_questions_v2_sample.json"

        if Path(questions_file).exists():
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            return {"success": True, "questions": questions}
        else:
            # Return simple questions if files not found
            return {
                "success": True,
                "questions": [
                    {
                        "key": "q1",
                        "question_ar": "في أي لحظات تحس الوقت يطير وأنت تمارس نشاط؟",
                        "question_en": "When do you feel time flies during an activity?",
                        "options": [
                            {"text_ar": "تركيز هادئ على تفصيلة واحدة", "text_en": "Calm focus on a single detail"},
                            {"text_ar": "أدرينالين وحركة سريعة", "text_en": "Adrenaline and fast movement"},
                            {"text_ar": "عمل جماعي متناغم", "text_en": "Harmonious teamwork"}
                        ]
                    }
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load questions: {str(e)}")

@app.get("/api/sports")
async def get_sports():
    """Get the list of available sports from the knowledge base"""
    import json

    try:
        sports_file = "data/knowledge/sports_catalog.json"

        if Path(sports_file).exists():
            with open(sports_file, 'r', encoding='utf-8') as f:
                catalog = json.load(f)

            # Return simplified list
            sports_list = []
            for sport in catalog.get("sports", []):
                sports_list.append({
                    "id": sport.get("id"),
                    "label": sport.get("label"),
                    "aliases": sport.get("aliases", []),
                    "risk_level": sport.get("risk_level", "low")
                })

            return {
                "success": True,
                "total_sports": len(sports_list),
                "sports": sports_list
            }
        else:
            return {
                "success": False,
                "error": "Sports catalog not found",
                "total_sports": 0,
                "sports": []
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sports: {str(e)}")

# Simple recommendation endpoint for testing
@app.post("/api/simple-recommend")
async def simple_recommend(request: dict):
    """
    Simplified recommendation endpoint for quick testing
    Accepts any JSON payload
    """
    try:
        return {
            "success": True,
            "message": "API is working!",
            "received": request,
            "recommendations": [
                "🧘 Yoga - Based on your calm nature",
                "🏃 Running - For your energetic side",
                "🎯 Archery - Perfect for focus"
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# This is required for Vercel
# The 'app' variable must be named 'app' for Vercel to find it
