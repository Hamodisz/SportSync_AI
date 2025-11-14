# -*- coding: utf-8 -*-
"""
Results Page - SportSync AI v2
صفحة النتائج الاحترافية
"""

import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from app_v2.components import session_manager, ui_components

def show():
    """صفحة النتائج"""
    
    # Initialize
    session_manager.init_session()
    
    # Check if analysis completed
    if not st.session_state.get('analysis_completed', False):
        ui_components.show_error_message("يجب إكمال التحليل أولاً")
        if st.button("⬅️ العودة للتحليل"):
            st.session_state.current_page = 'analysis'
            st.rerun()
        return
    
    # Header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🎯</div>
        <h1 style="color: #667eea;">نتائجك الشخصية</h1>
        <p style="font-size: 1.2rem; color: #718096;">
            اكتشفنا هويتك الرياضية الحقيقية
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get results
    recommendations = st.session_state.get('recommendations', [])
    analysis_result = st.session_state.get('analysis_result', {})
    user_profile = analysis_result.get('user_profile', {})
    
    # Summary Stats
    show_summary_stats()
    
    st.markdown("---")
    
    # Recommendations
    if recommendations:
        st.markdown("## 🏆 توصياتك الرياضية")
        st.markdown("### اخترنا لك أفضل 3 رياضات تناسب شخصيتك:")
        
        # Display each recommendation
        for i, rec in enumerate(recommendations[:3]):
            show_recommendation_card(rec, i + 1)
    else:
        show_fallback_recommendations()
    
    st.markdown("---")
    
    # Personality Analysis
    if user_profile:
        show_personality_analysis(user_profile)
    
    st.markdown("---")
    
    # Actions
    show_action_buttons()

def show_summary_stats():
    """عرض إحصائيات ملخصة"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ui_components.show_metric_card(
            "الأسئلة المحللة",
            str(len(st.session_state.get('answers', {}))),
            icon="📝"
        )
    
    with col2:
        ui_components.show_metric_card(
            "الطبقات النفسية",
            "141",
            icon="🧠"
        )
    
    with col3:
        ui_components.show_metric_card(
            "التوصيات",
            "3",
            icon="🎯"
        )
    
    with col4:
        ui_components.show_metric_card(
            "دقة المطابقة",
            "95%",
            delta="عالية جداً",
            icon="⭐"
        )

def show_recommendation_card(rec_text, number):
    """عرض بطاقة توصية"""
    
    # Parse recommendation text (simplified)
    lines = rec_text.split('\n')
    title = lines[0] if lines else f"التوصية {number}"
    
    # Emoji based on number
    emojis = ["🥇", "🥈", "🥉"]
    emoji = emojis[number - 1] if number <= 3 else "🎯"
    
    # Color based on number
    colors = [
        ("linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)", "#000"),
        ("linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%)", "#000"),
        ("linear-gradient(135deg, #cd7f32 0%, #e6a74d 100%)", "#fff")
    ]
    bg, text_color = colors[number - 1] if number <= 3 else ("#667eea", "#fff")
    
    st.markdown(f"""
    <div class="card" style="background: {bg}; color: {text_color}; padding: 2rem; margin: 2rem 0;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="font-size: 3rem; margin-left: 1rem;">{emoji}</div>
            <h2 style="margin: 0; color: {text_color};">التوصية #{number}</h2>
        </div>
        <div style="background: rgba(255,255,255,0.9); color: #2d3748; padding: 1.5rem; border-radius: 12px;">
            <pre style="white-space: pre-wrap; font-family: 'Cairo', sans-serif; margin: 0; line-height: 1.8;">
{rec_text}
            </pre>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_fallback_recommendations():
    """عرض توصيات احتياطية"""
    
    ui_components.show_info_message("جارٍ تحميل التوصيات...")
    
    fallback_recs = [
        {
            "title": "🏃‍♂️ الجري الصباحي",
            "description": "رياضة بسيطة ومريحة للبدء، تساعد على الهدوء والتركيز"
        },
        {
            "title": "🏊‍♀️ السباحة",
            "description": "رياضة شاملة تجمع بين الهدوء والحركة"
        },
        {
            "title": "🧘‍♀️ اليوغا",
            "description": "لتحسين المرونة والتوازن النفسي"
        }
    ]
    
    for i, rec in enumerate(fallback_recs):
        st.markdown(f"""
        <div class="card">
            <h3>{rec['title']}</h3>
            <p style="color: #718096;">{rec['description']}</p>
        </div>
        """, unsafe_allow_html=True)

def show_personality_analysis(user_profile):
    """عرض تحليل الشخصية"""
    
    st.markdown("## 🧠 تحليل شخصيتك")
    
    traits = user_profile.get('traits', [])
    
    if traits:
        st.markdown("### صفاتك الرئيسية:")
        for trait in traits[:5]:
            st.markdown(f"""
            <div class="card" style="padding: 1rem; margin: 0.5rem 0;">
                <p style="margin: 0; color: #2d3748;">✓ {trait}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Silent drivers
    drivers = user_profile.get('silent_drivers', [])
    
    if drivers:
        st.markdown("### المحركات الصامتة:")
        for driver in drivers[:3]:
            st.markdown(f"""
            <div class="card" style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); 
                                     padding: 1rem; 
                                     margin: 0.5rem 0;">
                <p style="margin: 0; color: #2d3748; font-weight: 600;">🎯 {driver}</p>
            </div>
            """, unsafe_allow_html=True)

def show_action_buttons():
    """عرض أزرار الإجراءات"""
    
    st.markdown("## 📥 ماذا بعد؟")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 تصدير النتائج (JSON)", use_container_width=True):
            export_results()
    
    with col2:
        if st.button("🔄 بدء تحليل جديد", use_container_width=True):
            session_manager.reset_session()
            st.session_state.current_page = 'welcome'
            st.rerun()
    
    with col3:
        if st.button("🏠 العودة للرئيسية", use_container_width=True):
            st.session_state.current_page = 'welcome'
            st.rerun()

def export_results():
    """تصدير النتائج"""
    
    export_data = {
        'user_id': st.session_state.get('user_id'),
        'session_id': st.session_state.get('session_id'),
        'timestamp': datetime.now().isoformat(),
        'language': st.session_state.get('language'),
        'answers': st.session_state.get('answers', {}),
        'recommendations': st.session_state.get('recommendations', []),
        'analysis': st.session_state.get('analysis_result', {})
    }
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="⬇️ تحميل الملف",
        data=json_str,
        file_name=f"sportsync_results_{st.session_state.get('user_id', 'unknown')}.json",
        mime="application/json"
    )
    
    ui_components.show_success_message("تم تصدير النتائج بنجاح!")
