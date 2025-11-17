# -*- coding: utf-8 -*-
"""
Questions Page - SportSync AI v2
صفحة الأسئلة المحسّنة والمتكاملة
"""

import streamlit as st
import json
from pathlib import Path
import sys

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from components import session_manager, ui_components

def load_questions():
    """تحميل الأسئلة"""
    lang = st.session_state.get('language', 'ar')

    # Try v2 questions first (10 deep questions with explicit scoring)
    file_name_v2 = 'arabic_questions_v2.json' if lang == 'ar' else 'english_questions_v2.json'
    questions_file_v2 = project_root / 'data' / 'questions' / file_name_v2

    # Fallback to old questions if v2 not found
    file_name_old = 'arabic_questions.json' if lang == 'ar' else 'english_questions.json'
    questions_file_old = project_root / 'data' / 'questions' / file_name_old

    try:
        # Try v2 first (in root directory)
        if questions_file_v2.exists():
            with open(questions_file_v2, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                print(f"[QUESTIONS] ✅ Loaded v2 questions: {len(questions)} questions")
                return questions  # v2 has exactly 10 questions
        else:
            # Fallback to old format
            with open(questions_file_old, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                print(f"[QUESTIONS] ⚠️ Using old format questions (fallback)")
                # Take first 20 questions
                return questions[:20]
    except Exception as e:
        st.error(f"خطأ في تحميل الأسئلة: {e}")
        return []

def show():
    """صفحة الأسئلة"""
    
    # Initialize session
    session_manager.init_session()
    
    # Load questions
    questions = load_questions()
    
    if not questions:
        ui_components.show_error_message("لم يتم العثور على الأسئلة")
        return
    
    # Update total
    st.session_state.total_questions = len(questions)
    
    # Current state
    current_idx = st.session_state.current_question
    total = len(questions)
    progress_info = session_manager.get_progress()
    
    # Check if completed
    if current_idx >= total:
        show_completion_screen()
        return
    
    # Header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>📝 الأسئلة</h1>
        <p style="font-size: 1.2rem; color: #718096;">
            سؤال {current_idx + 1} من {total}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    ui_components.show_progress_bar(
        progress_info['answered'],
        progress_info['total'],
        f"التقدم: {progress_info['percentage']}%"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Current question
    q = questions[current_idx]
    
    # Question card
    st.markdown(f"""
    <div class="card" style="background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%); 
                               padding: 3rem 2rem;
                               margin-bottom: 2rem;">
        <h2 style="color: #2d3748; text-align: center; margin-bottom: 0;">
            {q.get('question_ar', q.get('question_en', ''))}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Choices
    st.markdown("### اختر إجابتك:")

    # Handle both v2 format (options with text_ar/text_en) and old format (multiple_choices)
    if 'options' in q:
        # V2 format: extract text based on language
        lang_key = 'text_ar' if lang == 'ar' else 'text_en'
        choices = [opt.get(lang_key, opt.get('text_ar', '')) for opt in q['options']]
    else:
        # Old format: direct array of strings
        choices = q.get('multiple_choices', [])

    # Display choices as buttons
    cols = st.columns(1)
    for i, choice in enumerate(choices):
        if st.button(
            choice,
            key=f"choice_{current_idx}_{i}",
            use_container_width=True
        ):
            session_manager.save_answer(q['key'], choice)
            st.session_state.current_question += 1
            st.rerun()
    
    # Custom answer option
    if q.get('allow_custom', False):
        st.markdown("---")
        st.markdown("### 💭 أو اكتب إجابتك الخاصة:")
        
        custom = st.text_area(
            "",
            key=f"custom_{current_idx}",
            placeholder="اكتب هنا إجابتك المخصصة...",
            height=100
        )
        
        if st.button("التالي مع الإجابة المخصصة ➡️", use_container_width=True):
            if custom and custom.strip():
                session_manager.save_answer(q['key'], custom)
                st.session_state.current_question += 1
                st.rerun()
            else:
                ui_components.show_error_message("يرجى كتابة إجابة أولاً")
    
    # Navigation
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_idx > 0:
            if st.button("⬅️ السابق", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()
    
    with col2:
        # Show current answer if exists
        current_answer = st.session_state.answers.get(q['key'])
        if current_answer:
            st.info(f"إجابتك: {current_answer[:50]}...")
    
    with col3:
        if st.button("تخطي ⏭️", use_container_width=True, type="secondary"):
            st.session_state.current_question += 1
            st.rerun()

def show_completion_screen():
    """شاشة الإكمال"""
    
    progress_info = session_manager.get_progress()
    
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <div style="font-size: 5rem; margin-bottom: 1rem;">🎉</div>
        <h1 style="color: #48bb78;">أحسنت!</h1>
        <p style="font-size: 1.3rem; color: #718096;">
            أكملت جميع الأسئلة بنجاح
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ui_components.show_metric_card(
            "الأسئلة المجابة",
            f"{progress_info['answered']}/{progress_info['total']}",
            icon="📝"
        )
    
    with col2:
        ui_components.show_metric_card(
            "نسبة الإكمال",
            f"{progress_info['percentage']}%",
            icon="📊"
        )
    
    with col3:
        ui_components.show_metric_card(
            "الوقت المتوقع للتحليل",
            "30-60 ثانية",
            icon="⏱️"
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # CTA
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🧠 ابدأ التحليل العميق", use_container_width=True, type="primary"):
            st.session_state.questions_completed = True
            st.session_state.current_page = 'analysis'
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔄 إعادة الأسئلة", use_container_width=True, type="secondary"):
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.rerun()
