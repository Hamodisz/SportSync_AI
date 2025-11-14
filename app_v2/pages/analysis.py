# -*- coding: utf-8 -*-
"""
Analysis Page - SportSync AI v2
صفحة التحليل الحقيقية مع Layer-Z
"""

import streamlit as st
import sys
from pathlib import Path
import time
import json

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from app_v2.components import session_manager, ui_components

def run_analysis():
    """تشغيل التحليل الفعلي"""
    
    try:
        # Import analysis modules
        from analysis.layer_z_enhanced import LayerZEnhanced
        from analysis.user_analysis import analyze_user
        
        # Get answers
        answers = st.session_state.get('answers', {})
        
        if not answers:
            return None, "لا توجد إجابات للتحليل"
        
        # Step 1: Layer-Z Analysis
        st.session_state.analysis_step = "Layer-Z Analysis"
        layer_z = LayerZEnhanced()
        
        # Convert answers to format
        answers_text = "\n".join([f"{k}: {v}" for k, v in answers.items()])
        
        z_result = layer_z.analyze({"answers": answers_text})
        
        time.sleep(1)  # Simulate processing
        
        # Step 2: User Analysis (141 layers)
        st.session_state.analysis_step = "141 Layer Analysis"
        
        user_profile = analyze_user(answers)
        
        time.sleep(1)
        
        # Step 3: Generate Recommendations
        st.session_state.analysis_step = "Generating Recommendations"
        
        from core.backend_gpt import generate_sport_recommendation
        
        recommendations = generate_sport_recommendation(
            answers=answers,
            lang=st.session_state.get('language', 'ar'),
            user_id=st.session_state.get('user_id'),
            job_id=st.session_state.get('session_id')
        )
        
        # Combine results
        result = {
            'layer_z': z_result,
            'user_profile': user_profile,
            'recommendations': recommendations,
            'timestamp': time.time()
        }
        
        return result, None
        
    except Exception as e:
        return None, f"خطأ في التحليل: {str(e)}"

def show():
    """صفحة التحليل"""
    
    # Initialize
    session_manager.init_session()
    
    # Check if questions completed
    if not st.session_state.get('questions_completed', False):
        ui_components.show_error_message("يجب إكمال الأسئلة أولاً")
        if st.button("⬅️ العودة للأسئلة"):
            st.session_state.current_page = 'questions'
            st.rerun()
        return
    
    # Header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1>🧠 التحليل العميق</h1>
        <p style="font-size: 1.2rem; color: #718096;">
            جارٍ تحليل إجاباتك بعمق...
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if already analyzed
    if st.session_state.get('analysis_completed', False):
        show_analysis_summary()
        return
    
    # Show analysis steps
    show_analysis_progress()
    
    # Run analysis
    if not st.session_state.get('analysis_started', False):
        st.session_state.analysis_started = True
        
        # Progress placeholder
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Simulate analysis steps
        steps = [
            ("🔍 تحليل الإجابات", 10),
            ("🧠 محرك Layer-Z", 25),
            ("📊 141 طبقة نفسية", 50),
            ("🎯 المطابقة الذكية", 75),
            ("✨ التوصيات النهائية", 90),
        ]
        
        for step_name, progress_value in steps:
            status_placeholder.markdown(f"### {step_name}")
            progress_placeholder.progress(progress_value / 100)
            time.sleep(1.5)
        
        # Final progress
        progress_placeholder.progress(1.0)
        status_placeholder.markdown("### ✅ اكتمل التحليل!")
        
        time.sleep(1)
        
        # Run actual analysis
        with st.spinner("جارٍ معالجة النتائج..."):
            result, error = run_analysis()
            
            if error:
                ui_components.show_error_message(error)
                st.session_state.analysis_started = False
                return
            
            # Save results
            st.session_state.analysis_result = result
            st.session_state.layer_z_result = result.get('layer_z')
            st.session_state.recommendations = result.get('recommendations')
            st.session_state.analysis_completed = True
        
        # Redirect to results
        time.sleep(1)
        st.session_state.current_page = 'results'
        st.rerun()

def show_analysis_progress():
    """عرض تقدم التحليل"""
    
    st.markdown("## ⚙️ ما يحدث الآن:")
    
    steps_info = [
        {
            "icon": "🔍",
            "title": "تحليل الإجابات",
            "description": "فهم كل إجابة والسياق"
        },
        {
            "icon": "🧠",
            "title": "محرك Layer-Z",
            "description": "كشف المحركات الصامتة والنوايا العميقة"
        },
        {
            "icon": "📊",
            "title": "141 طبقة نفسية",
            "description": "تحليل شامل للشخصية والسلوك"
        },
        {
            "icon": "🎯",
            "title": "المطابقة الذكية",
            "description": "البحث في 8000+ رياضة"
        },
        {
            "icon": "✨",
            "title": "التوصيات النهائية",
            "description": "اختيار أفضل 3 رياضات لك"
        }
    ]
    
    for step in steps_info:
        st.markdown(f"""
        <div class="card" style="display: flex; align-items: center; padding: 1.5rem;">
            <div style="font-size: 2.5rem; margin-left: 1rem;">{step['icon']}</div>
            <div>
                <h3 style="margin: 0; color: #2d3748;">{step['title']}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #718096;">{step['description']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

def show_analysis_summary():
    """عرض ملخص التحليل"""
    
    ui_components.show_success_message("اكتمل التحليل بنجاح!")
    
    st.markdown("## 📊 ملخص التحليل:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ui_components.show_metric_card(
            "الأسئلة المحللة",
            str(len(st.session_state.get('answers', {}))),
            icon="📝"
        )
    
    with col2:
        ui_components.show_metric_card(
            "الطبقات المحللة",
            "141",
            icon="🧠"
        )
    
    with col3:
        ui_components.show_metric_card(
            "التوصيات",
            "3",
            icon="🎯"
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🎯 شاهد النتائج", use_container_width=True, type="primary"):
            st.session_state.current_page = 'results'
            st.rerun()
