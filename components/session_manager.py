# -*- coding: utf-8 -*-
"""
Session Manager - SportSync AI v2
إدارة الجلسات والحالة
"""

import streamlit as st
import uuid
from datetime import datetime

def init_session():
    """تهيئة الجلسة"""
    
    # User ID
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    
    # Session ID
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Timestamps
    if 'session_start' not in st.session_state:
        st.session_state.session_start = datetime.now()
    
    # Language
    if 'language' not in st.session_state:
        st.session_state.language = 'ar'
    
    # Navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'welcome'
    
    # Questions
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    if 'total_questions' not in st.session_state:
        st.session_state.total_questions = 20
    
    # Flags
    if 'started' not in st.session_state:
        st.session_state.started = False
    
    if 'questions_completed' not in st.session_state:
        st.session_state.questions_completed = False
    
    if 'analysis_started' not in st.session_state:
        st.session_state.analysis_started = False
    
    if 'analysis_completed' not in st.session_state:
        st.session_state.analysis_completed = False
    
    # Results
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    
    if 'layer_z_result' not in st.session_state:
        st.session_state.layer_z_result = None

def reset_session():
    """إعادة تعيين الجلسة"""
    keys_to_keep = ['user_id', 'language']
    keys_to_remove = [key for key in st.session_state.keys() if key not in keys_to_keep]
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    init_session()

def get_session_info():
    """الحصول على معلومات الجلسة"""
    return {
        'user_id': st.session_state.get('user_id'),
        'session_id': st.session_state.get('session_id'),
        'language': st.session_state.get('language'),
        'started': st.session_state.get('started'),
        'questions_completed': st.session_state.get('questions_completed'),
        'answers_count': len(st.session_state.get('answers', {})),
        'current_page': st.session_state.get('current_page'),
    }

def save_answer(question_key, answer_value):
    """حفظ إجابة"""
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    st.session_state.answers[question_key] = answer_value

def get_progress():
    """الحصول على التقدم"""
    total = st.session_state.get('total_questions', 20)
    answered = len(st.session_state.get('answers', {}))
    
    return {
        'answered': answered,
        'total': total,
        'percentage': int((answered / total) * 100) if total > 0 else 0,
        'remaining': total - answered
    }
