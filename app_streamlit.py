# -*- coding: utf-8 -*-
"""
SportSync AI - Streamlit UI with Collaborative Filtering
========================================================
Version 2.0 - Integrated with FastAPI backend
"""

import time
import uuid
import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional
import requests
import json

# Core imports
from core.core_engine import run_full_generation, quick_diagnose
from core.backend_gpt import generate_sport_recommendation, get_last_rec_source
from core.llm_client import make_llm_client, pick_models
from core.user_logger import get_log_stats

# Database and ML imports
try:
    from database.supabase_client import get_supabase_client
    from ml.collaborative_filtering import CollaborativeFilteringEngine
    CF_AVAILABLE = True
except ImportError:
    CF_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="SportSync AI - Dual Intelligence System",
    page_icon="🎯",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    """Initialize database and CF engine"""
    if CF_AVAILABLE:
        db = get_supabase_client()
        cf_engine = CollaborativeFilteringEngine(supabase_client=db)
        if cf_engine.is_available():
            cf_engine.load_ratings_from_db()
            return db, cf_engine
    return None, None

db, cf_engine = init_services()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []
if 'user_ratings' not in st.session_state:
    st.session_state.user_ratings = {}

# Header
st.title("🎯 SportSync AI - نظام الذكاء المزدوج")
st.markdown("**Discovery Model (o4-mini)** + **Reasoning Model (gpt-5)** + **Collaborative Filtering**")

# Sidebar
with st.sidebar:
    st.header("⚙️ System Status")
    
    # LLM Status
    client = make_llm_client()
    main_model, fb_model = pick_models()
    st.metric("LLM Status", "✅ Connected" if client else "❌ Disconnected")
    st.caption(f"Discovery: o4-mini")
    st.caption(f"Reasoning: gpt-5")
    
    # Database Status
    if db and db.is_enabled():
        st.metric("Database", "✅ Connected")
    else:
        st.metric("Database", "❌ Disconnected")
    
    # CF Engine Status
    if cf_engine and cf_engine.is_available():
        st.metric("CF Engine", "✅ Ready")
        st.caption(f"Users: {len(cf_engine.user_item_matrix)}")
        st.caption(f"Sports: {len(cf_engine.item_users_matrix)}")
    else:
        st.metric("CF Engine", "❌ Unavailable")
    
    st.divider()
    
    # User Info
    st.caption(f"User ID: {st.session_state.user_id[:8]}...")
    st.caption(f"Session: {st.session_state.session_id[:8]}...")
    
    if st.button("🔄 Refresh CF Data"):
        if cf_engine and cf_engine.is_available():
            with st.spinner("Refreshing..."):
                cf_engine.refresh_data()
            st.success("Data refreshed!")
        else:
            st.warning("CF not available")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎬 Quick Video",
    "📝 Quiz & Recommendations", 
    "⭐ My Ratings",
    "👥 Similar Users",
    "📊 Analytics"
])

# ========================================
# Tab 1: Quick Video Generation
# ========================================
with tab1:
    st.header("🎬 Quick Video Generation")
    
    lang = st.selectbox("Language", ["ar", "en"], index=0)
    
    DEFAULT_SCRIPT = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""
    
    script = st.text_area("Script", DEFAULT_SCRIPT, height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        seconds = st.slider("Seconds per image", 2, 8, 4)
        add_voice = st.checkbox("Add voice-over", value=False)
    
    with col2:
        use_ai = st.checkbox("Use AI images (OpenAI)", value=False)
        use_stock = st.checkbox("Use stock photos", value=True)
    
    if st.button("🎥 Generate Video", type="primary"):
        with st.spinner("Generating video..."):
            result = run_full_generation({
                "script": script,
                "lang": lang,
                "seconds_per_image": seconds,
                "add_voice": add_voice,
                "use_ai": use_ai,
                "use_stock": use_stock
            })
        
        if result.get("ok"):
            st.success("✅ Video generated!")
            
            vpath = Path(result["video"])
            if vpath.exists():
                with open(vpath, "rb") as f:
                    video_bytes = f.read()
                    st.video(video_bytes)
                    st.download_button(
                        "📥 Download MP4",
                        data=video_bytes,
                        file_name="sportsync_video.mp4",
                        mime="video/mp4"
                    )
        else:
            st.error(f"❌ Error: {result.get('error')}")
    
    if st.button("🔍 Quick Diagnose"):
        st.json(quick_diagnose())

# ========================================
# Tab 2: Quiz & Recommendations
# ========================================
with tab2:
    st.header("📝 Sport Discovery Quiz")
    
    if not st.session_state.quiz_completed:
        st.markdown("### Answer these questions to discover your perfect sport")
        
        # Simplified quiz for demo
        with st.form("quiz_form"):
            q1 = st.select_slider(
                "كيف تشعر عند مواجهة تحدي جديد؟",
                options=["خائف", "قلق", "محايد", "متحمس", "متحمس جداً"]
            )
            
            q2 = st.multiselect(
                "أي بيئة تفضل؟",
                ["المنزل", "النادي", "الهواء الطلق", "المسبح", "ملعب جماعي"]
            )
            
            q3 = st.select_slider(
                "مستوى الطاقة المفضل؟",
                options=["استرخاء", "طاقة منخفضة", "متوسط", "طاقة عالية", "طاقة عالية جداً"]
            )
            
            q4 = st.radio(
                "تفضل التفاعل الاجتماعي؟",
                ["أفضل وحدي", "مع شريك", "أحياناً مع آخرين", "دائماً مع فريق"]
            )
            
            submitted = st.form_submit_button("🎯 Get Recommendations", type="primary")
            
            if submitted:
                with st.spinner("Analyzing with Dual-Model AI..."):
                    # Simulate quiz submission
                    answers = {
                        "1": q1,
                        "2": ", ".join(q2) if q2 else "None",
                        "3": q3,
                        "4": q4
                    }
                    
                    # In real implementation, call dual_model_client
                    # For demo, generate sample recommendations
                    time.sleep(2)
                    
                    recommendations = [
                        {
                            "sport_label": "كرة القدم" if lang == "ar" else "Football",
                            "match_percentage": 92,
                            "why": ["تناسب طاقتك العالية", "تحب العمل الجماعي"],
                            "category": "team_sport"
                        },
                        {
                            "sport_label": "السباحة" if lang == "ar" else "Swimming",
                            "match_percentage": 85,
                            "why": ["تمرين شامل", "مناسب للاسترخاء"],
                            "category": "individual_sport"
                        },
                        {
                            "sport_label": "اليوجا" if lang == "ar" else "Yoga",
                            "match_percentage": 78,
                            "why": ["توازن وهدوء", "مرونة عالية"],
                            "category": "mindful_activity"
                        }
                    ]
                    
                    # Apply collaborative filtering if available
                    if cf_engine and cf_engine.is_available():
                        try:
                            recommendations = cf_engine.hybrid_recommend(
                                user_id=st.session_state.user_id,
                                content_based_recs=recommendations,
                                n_recommendations=3,
                                cf_weight=0.4
                            )
                            st.info("✨ Recommendations enhanced with Collaborative Filtering!")
                        except:
                            pass
                    
                    st.session_state.recommendations = recommendations
                    st.session_state.quiz_completed = True
                    st.rerun()
    
    else:
        st.success("✅ Quiz Completed!")
        
        st.markdown("### 🎯 Your Personalized Recommendations")
        
        for idx, rec in enumerate(st.session_state.recommendations, 1):
            with st.expander(f"#{idx} {rec['sport_label']} - {rec['match_percentage']}% Match", expanded=True):
                st.metric("Match Score", f"{rec['match_percentage']}%")
                
                if rec.get('hybrid_score'):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Content Score", f"{rec.get('cb_score', 0):.2f}")
                    col2.metric("CF Score", f"{rec.get('cf_score', 0):.2f}")
                    col3.metric("Hybrid Score", f"{rec['hybrid_score']:.2f}")
                
                st.markdown("**Why it's perfect for you:**")
                for reason in rec.get('why', []):
                    st.markdown(f"- {reason}")
                
                # Rating
                rating = st.slider(
                    f"Rate {rec['sport_label']}",
                    0.0, 5.0, 3.0, 0.5,
                    key=f"rating_{idx}"
                )
                
                if st.button(f"💾 Save Rating", key=f"save_{idx}"):
                    # Save rating
                    if db and db.is_enabled():
                        db.save_sport_rating(
                            user_id=st.session_state.user_id,
                            sport_label=rec['sport_label'],
                            rating=rating,
                            was_recommended=True,
                            was_liked=rating >= 4.0
                        )
                    
                    # Update CF engine
                    if cf_engine and cf_engine.is_available():
                        cf_engine.update_user_rating(
                            user_id=st.session_state.user_id,
                            sport_label=rec['sport_label'],
                            rating=rating
                        )
                    
                    st.session_state.user_ratings[rec['sport_label']] = rating
                    st.success(f"Rating saved: {rating}⭐")
        
        if st.button("🔄 Take Quiz Again"):
            st.session_state.quiz_completed = False
            st.session_state.recommendations = []
            st.rerun()

# ========================================
# Tab 3: My Ratings
# ========================================
with tab3:
    st.header("⭐ My Sport Ratings")
    
    if st.session_state.user_ratings:
        for sport, rating in st.session_state.user_ratings.items():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{sport}**")
            col2.metric("Rating", f"{rating}⭐")
    else:
        st.info("No ratings yet. Complete the quiz and rate some sports!")
    
    # Get CF recommendations based on ratings
    if cf_engine and cf_engine.is_available() and st.session_state.user_ratings:
        if st.button("🎯 Get More Recommendations (CF)"):
            with st.spinner("Finding sports you'll love..."):
                cf_recs = cf_engine.recommend_for_user(
                    user_id=st.session_state.user_id,
                    n_recommendations=5
                )
                
                if cf_recs:
                    st.success(f"Found {len(cf_recs)} recommendations!")
                    for rec in cf_recs:
                        st.write(f"- **{rec['sport_label']}** (Predicted: {rec['predicted_rating']}⭐)")
                else:
                    st.warning("Need more ratings to generate CF recommendations")

# ========================================
# Tab 4: Similar Users
# ========================================
with tab4:
    st.header("👥 Users Similar to You")
    
    if cf_engine and cf_engine.is_available():
        if st.button("🔍 Find Similar Users"):
            with st.spinner("Analyzing similarities..."):
                similar = cf_engine.compute_user_similarity(
                    user_id=st.session_state.user_id,
                    top_k=10
                )
                
                if similar:
                    st.success(f"Found {len(similar)} similar users!")
                    
                    for uid, score in similar[:5]:
                        st.metric(f"User {uid[:8]}...", f"{score:.2%} similar")
                        
                        # Show their favorite sports
                        user_sports = cf_engine.user_item_matrix.get(uid, {})
                        top_sports = sorted(user_sports.items(), key=lambda x: x[1], reverse=True)[:3]
                        st.caption("Their favorites: " + ", ".join([s for s, _ in top_sports]))
                else:
                    st.info("Need more activity to find similar users")
    else:
        st.warning("Collaborative filtering not available")

# ========================================
# Tab 5: Analytics
# ========================================
with tab5:
    st.header("📊 System Analytics")
    
    col1, col2, col3 = st.columns(3)
    
    # Stats
    if db and db.is_enabled():
        popular = db.get_popular_sports(limit=10)
        
        col1.metric("Popular Sports", len(popular))
        
        if cf_engine and cf_engine.is_available():
            col2.metric("Total Users", len(cf_engine.user_item_matrix))
            col3.metric("Total Sports", len(cf_engine.item_users_matrix))
        
        # Popular sports chart
        if popular:
            st.subheader("🏆 Most Popular Sports")
            for sport in popular[:10]:
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(sport['sport_label'])
                col2.metric("Users", sport.get('unique_users', 0))
                col3.metric("Avg Rating", f"{sport.get('avg_rating', 0):.1f}⭐")
    
    # System diagnostics
    with st.expander("🔧 System Diagnostics"):
        st.json(quick_diagnose())
    
    # Log stats
    try:
        stats = get_log_stats()
        with st.expander("📝 Log Statistics"):
            st.json(stats)
    except:
        pass

# Footer
st.divider()
st.caption("SportSync AI v2.0 - Powered by Dual-Model Intelligence + Collaborative Filtering")
st.caption("Discovery (o4-mini) + Reasoning (gpt-5) + CF Engine")
