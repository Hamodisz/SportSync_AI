# -*- coding: utf-8 -*-
"""
FastAPI Server for SportSync AI
================================
RESTful API for quiz, recommendations, and collaborative filtering
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# SportSync imports
from database.supabase_client import get_supabase_client
from ml.collaborative_filtering import CollaborativeFilteringEngine
from core.dual_model_client import (
    analyze_user_with_discovery,
    generate_deep_recommendations_with_reasoning
)

# Initialize FastAPI
app = FastAPI(
    title="SportSync AI API",
    description="Intelligent sport recommendation system with collaborative filtering",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = get_supabase_client()
cf_engine = CollaborativeFilteringEngine(supabase_client=db)

# Load CF data on startup
@app.on_event("startup")
async def startup_event():
    """Load collaborative filtering data on startup"""
    if cf_engine.is_available():
        cf_engine.load_ratings_from_db()
        print("[API] Collaborative filtering engine loaded")
    else:
        print("[API] CF engine not available - will use content-based only")

# ========================================
# Request/Response Models
# ========================================

class QuizAnswer(BaseModel):
    question_id: str
    question_text: str
    answer: str
    answer_index: Optional[int] = None
    category: Optional[str] = None

class QuizSubmission(BaseModel):
    user_identifier: str = Field(..., description="Anonymous user identifier (email, device_id, etc.)")
    language: str = Field(default="ar", description="ar or en")
    answers: List[QuizAnswer]
    identity_scores: Optional[Dict[str, float]] = None
    trait_scores: Optional[Dict[str, float]] = None

class RecommendationResponse(BaseModel):
    session_id: str
    user_id: str
    recommendations: List[Dict[str, Any]]
    cf_enabled: bool
    hybrid_mode: bool

class RatingSubmission(BaseModel):
    user_identifier: str
    sport_label: str
    rating: float = Field(..., ge=0.0, le=5.0)
    was_recommended: bool = False
    was_clicked: bool = False
    was_liked: Optional[bool] = None

class SimilarUsersResponse(BaseModel):
    user_id: str
    similar_users: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]

# ========================================
# Endpoints
# ========================================

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "healthy",
        "service": "SportSync AI API",
        "version": "2.0.0",
        "features": {
            "database": db.is_enabled(),
            "collaborative_filtering": cf_engine.is_available(),
            "dual_model_ai": True
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected" if db.is_enabled() else "disconnected",
            "cf_engine": "ready" if cf_engine.is_available() else "unavailable",
            "users_in_cf": len(cf_engine.user_item_matrix) if cf_engine.is_available() else 0,
            "sports_in_cf": len(cf_engine.item_users_matrix) if cf_engine.is_available() else 0
        }
    }

@app.post("/api/v1/quiz/submit", response_model=RecommendationResponse)
async def submit_quiz(
    submission: QuizSubmission,
    background_tasks: BackgroundTasks
):
    """
    Submit quiz answers and get personalized recommendations
    
    Uses dual-model AI system:
    - Discovery Model (o4-mini): Quick pattern analysis
    - Reasoning Model (gpt-5): Deep recommendations
    
    If collaborative filtering is enabled, recommendations are hybrid (CF + content-based)
    """
    try:
        # Generate user hash
        user_hash = db.generate_user_hash(submission.user_identifier)
        
        # Create or get user
        user = db.create_or_get_user(
            user_hash=user_hash,
            language=submission.language
        ) if db.is_enabled() else {'id': str(uuid.uuid4())}
        
        user_id = user['id']
        session_id = str(uuid.uuid4())
        
        # Convert answers to dict format
        answers_dict = {
            ans.question_id: ans.answer 
            for ans in submission.answers
        }
        
        # Phase 1: Quick Discovery Analysis (o4-mini)
        quick_analysis = analyze_user_with_discovery(
            answers=answers_dict,
            identity=submission.identity_scores or {},
            traits=submission.trait_scores or {},
            lang=submission.language
        )
        
        # Extract drivers from quick analysis
        drivers = quick_analysis.get('patterns', [])
        if isinstance(drivers, dict):
            drivers = list(drivers.keys())
        
        # Phase 2: Deep Reasoning Recommendations (gpt-5)
        content_based_recs = generate_deep_recommendations_with_reasoning(
            quick_analysis=quick_analysis,
            drivers=drivers,
            lang=submission.language
        ) or []
        
        # Phase 3: Collaborative Filtering (if available)
        hybrid_mode = False
        if cf_engine.is_available() and len(content_based_recs) > 0:
            # Check if user has enough history
            user_ratings = cf_engine.user_item_matrix.get(user_id, {})
            
            if len(user_ratings) >= 3:  # Need minimum history for CF
                content_based_recs = cf_engine.hybrid_recommend(
                    user_id=user_id,
                    content_based_recs=content_based_recs,
                    n_recommendations=5,
                    cf_weight=0.4
                )
                hybrid_mode = True
        
        # Save to database (background)
        if db.is_enabled():
            background_tasks.add_task(
                save_quiz_data_background,
                user_id, session_id, submission, content_based_recs, submission.trait_scores or {}
            )
        
        return RecommendationResponse(
            session_id=session_id,
            user_id=user_id,
            recommendations=content_based_recs[:3],
            cf_enabled=cf_engine.is_available(),
            hybrid_mode=hybrid_mode
        )
        
    except Exception as e:
        print(f"[API] Error in submit_quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/rating/submit")
async def submit_rating(rating: RatingSubmission):
    """Submit a sport rating (for collaborative filtering)"""
    try:
        user_hash = db.generate_user_hash(rating.user_identifier)
        
        # Get user
        user = db.create_or_get_user(user_hash=user_hash) if db.is_enabled() else None
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        # Save rating to database
        success = db.save_sport_rating(
            user_id=user_id,
            sport_label=rating.sport_label,
            rating=rating.rating,
            was_recommended=rating.was_recommended,
            was_clicked=rating.was_clicked,
            was_liked=rating.was_liked
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save rating")
        
        # Update CF engine
        if cf_engine.is_available():
            cf_engine.update_user_rating(
                user_id=user_id,
                sport_label=rating.sport_label,
                rating=rating.rating,
                save_to_db=False  # Already saved above
            )
        
        return {
            "status": "success",
            "message": "Rating saved successfully",
            "user_id": user_id,
            "sport": rating.sport_label
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error in submit_rating: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/recommendations/{user_identifier}")
async def get_recommendations(user_identifier: str, n: int = 10):
    """Get collaborative filtering recommendations for a user"""
    try:
        if not cf_engine.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Collaborative filtering not available"
            )
        
        user_hash = db.generate_user_hash(user_identifier)
        user = db.create_or_get_user(user_hash=user_hash) if db.is_enabled() else None
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        # Get CF recommendations
        recs = cf_engine.recommend_for_user(user_id, n_recommendations=n)
        
        return {
            "user_id": user_id,
            "recommendations": recs,
            "count": len(recs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error in get_recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/similar-users/{user_identifier}", response_model=SimilarUsersResponse)
async def get_similar_users(user_identifier: str, top_k: int = 10):
    """Get similar users and their favorite sports"""
    try:
        if not cf_engine.is_available():
            raise HTTPException(
                status_code=503,
                detail="Collaborative filtering not available"
            )
        
        user_hash = db.generate_user_hash(user_identifier)
        user = db.create_or_get_user(user_hash=user_hash) if db.is_enabled() else None
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user['id']
        
        # Compute similar users
        similar_users = cf_engine.compute_user_similarity(user_id, top_k=top_k)
        
        # Get recommendations from similar users
        recs = cf_engine.recommend_for_user(user_id, n_recommendations=10)
        
        return SimilarUsersResponse(
            user_id=user_id,
            similar_users=[
                {"user_id": uid, "similarity_score": score}
                for uid, score in similar_users
            ],
            recommendations=recs
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error in get_similar_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/popular-sports")
async def get_popular_sports(limit: int = 20):
    """Get most popular sports across all users"""
    try:
        if not db.is_enabled():
            raise HTTPException(status_code=503, detail="Database not available")
        
        popular = db.get_popular_sports(limit=limit)
        
        return {
            "sports": popular,
            "count": len(popular)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error in get_popular_sports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/refresh-cf")
async def refresh_collaborative_filtering(background_tasks: BackgroundTasks):
    """Refresh collaborative filtering data (admin endpoint)"""
    try:
        if not cf_engine.is_available():
            raise HTTPException(
                status_code=503,
                detail="Collaborative filtering not available"
            )
        
        # Refresh in background
        background_tasks.add_task(cf_engine.refresh_data)
        
        return {
            "status": "refreshing",
            "message": "Collaborative filtering data refresh initiated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Error in refresh_cf: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Background Tasks
# ========================================

def save_quiz_data_background(
    user_id: str,
    session_id: str,
    submission: QuizSubmission,
    recommendations: List[Dict],
    traits: Dict[str, float]
):
    """Save quiz data to database (background task)"""
    try:
        # Save quiz responses
        responses = [
            {
                'question_id': ans.question_id,
                'question_text': ans.question_text,
                'answer': ans.answer,
                'answer_index': ans.answer_index,
                'category': ans.category
            }
            for ans in submission.answers
        ]
        db.save_quiz_responses(user_id, session_id, responses)
        
        # Save traits
        if traits:
            db.save_user_traits(user_id, session_id, traits)
        
        # Save recommendations
        if recommendations:
            db.save_recommendations(user_id, session_id, recommendations)
        
        # Log analytics event
        db.log_event(
            user_id=user_id,
            event_type='quiz_completed',
            event_data={'num_questions': len(submission.answers)},
            session_id=session_id
        )
        
        print(f"[API] Background save completed for user {user_id[:8]}...")
        
    except Exception as e:
        print(f"[API] Error in background save: {e}")


# ========================================
# Run Server
# ========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
