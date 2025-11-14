# -*- coding: utf-8 -*-
"""
SportSync AI v2 - Next Generation
==================================
نسخة محسّنة ومطوّرة مع MCP Integration
"""

import streamlit as st
import sys
from pathlib import Path

# إضافة المسار الأساسي
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SportSync AI v2 - اكتشف رياضتك الحقيقية",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://sportsync.ai/help',
        'Report a bug': "https://github.com/sportsync/issues",
        'About': """
        # SportSync AI v2 🚀
        
        **الجيل الثاني** من نظام اكتشاف الهوية الرياضية
        
        ## 🆕 الجديد في v2:
        - 🎨 UI عصري ومحسّن
        - ⚡ أداء أسرع 3x
        - 🧠 MCP Integration
        - 📊 Dashboard متقدم
        - 🎥 فيديوهات تفاعلية
        
        ## 💪 القوة:
        - 141 طبقة تحليل نفسي
        - محرك Layer-Z المحسّن
        - 8000+ رياضة ونشاط
        - AI-powered recommendations
        """
    }
)

# ══════════════════════════════════════════════════════════════
# CUSTOM CSS - Modern Design
# ══════════════════════════════════════════════════════════════

def inject_custom_css():
    """تحميل CSS حديث وعصري"""
    st.markdown("""
    <style>
    /* ===== Import Fonts ===== */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ===== Global Styles ===== */
    * {
        font-family: 'Cairo', 'Inter', sans-serif !important;
    }
    
    /* ===== Main Container ===== */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0 !important;
    }
    
    /* ===== Content Container ===== */
    .block-container {
        padding: 2rem 3rem !important;
        max-width: 1400px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        margin: 2rem auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
    }
    
    /* ===== Headers ===== */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    h2 {
        color: #2d3748;
        font-weight: 700 !important;
        font-size: 2rem !important;
        margin: 2rem 0 1rem 0;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #4a5568;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
    }
    
    /* ===== Buttons ===== */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* ===== Cards ===== */
    .card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.2);
    }
    
    /* ===== Progress Bar ===== */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* ===== Metrics ===== */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #667eea;
    }
    
    /* ===== Animations ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* ===== Success/Error Messages ===== */
    .stSuccess {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
    }
    
    .stError {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
    }
    
    /* ===== Language Switcher ===== */
    .language-switcher {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: white;
        padding: 0.5rem 1rem;
        border-radius: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* ===== Custom Scrollbar ===== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
    </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════

def init_session_state():
    """تهيئة Session State"""
    defaults = {
        'current_page': 'welcome',
        'language': 'ar',
        'user_id': None,
        'answers': {},
        'analysis_result': None,
        'recommendations': None,
        'current_question': 0,
        'total_questions': 20,
        'started': False,
        'completed': False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ══════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════

def main():
    """التطبيق الرئيسي"""
    
    # تحميل CSS
    inject_custom_css()
    
    # تهيئة Session State
    init_session_state()
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("# 🚀 SportSync AI v2")
        st.markdown("---")
        
        # Language Switcher
        lang = st.radio(
            "🌐 اللغة / Language",
            options=['ar', 'en'],
            format_func=lambda x: "🇸🇦 العربية" if x == 'ar' else "🇬🇧 English",
            key='language'
        )
        
        st.markdown("---")
        
        # Navigation
        pages = {
            'welcome': '🏠 الرئيسية',
            'questions': '📝 الأسئلة',
            'analysis': '🧠 التحليل',
            'results': '🎯 النتائج'
        }
        
        st.markdown("### 📍 التنقل")
        for page_key, page_name in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # Progress
        if st.session_state.started:
            st.markdown("### 📊 التقدم")
            progress = st.session_state.current_question / st.session_state.total_questions
            st.progress(progress)
            st.caption(f"{st.session_state.current_question}/{st.session_state.total_questions} أسئلة")
        
        # Footer
        st.markdown("---")
        st.markdown("### 💡 معلومات")
        st.info("""
        **SportSync AI v2**
        
        الجيل الثاني من نظام اكتشاف الهوية الرياضية
        
        🧠 141 طبقة تحليل
        🎯 8000+ رياضة
        ⚡ AI-Powered
        """)
    
    # ══════════════════════════════════════════════════════════
    # PAGE ROUTING
    # ══════════════════════════════════════════════════════════
    
    page = st.session_state.current_page
    
    if page == 'welcome':
        from pages import welcome
        welcome.show()
    
    elif page == 'questions':
        from pages import questions
        questions.show()
    
    elif page == 'analysis':
        from pages import analysis
        analysis.show()
    
    elif page == 'results':
        from pages import results
        results.show()
    
    else:
        st.error("صفحة غير موجودة!")

if __name__ == "__main__":
    main()

# Import components
from components import session_manager

# ══════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════

def main():
    """التطبيق الرئيسي"""
    
    # تحميل CSS
    inject_custom_css()
    
    # تهيئة Session State
    session_manager.init_session()
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("# 🚀 SportSync AI v2")
        st.markdown("---")
        
        # Language Switcher
        lang = st.radio(
            "🌐 اللغة / Language",
            options=['ar', 'en'],
            format_func=lambda x: "🇸🇦 العربية" if x == 'ar' else "🇬🇧 English",
            key='language'
        )
        
        st.markdown("---")
        
        # Navigation
        pages = {
            'welcome': '🏠 الرئيسية',
            'questions': '📝 الأسئلة',
            'analysis': '🧠 التحليل',
            'results': '🎯 النتائج'
        }
        
        st.markdown("### 📍 التنقل")
        for page_key, page_name in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # Progress
        if st.session_state.get('started', False):
            progress_info = session_manager.get_progress()
            st.markdown("### 📊 التقدم")
            st.progress(progress_info['percentage'] / 100)
            st.caption(f"{progress_info['answered']}/{progress_info['total']} أسئلة")
            st.caption(f"{progress_info['percentage']}% مكتمل")
        
        # Session Info
        st.markdown("---")
        st.markdown("### 💡 معلومات الجلسة")
        session_info = session_manager.get_session_info()
        st.caption(f"👤 User: {session_info['user_id'][:8]}...")
        st.caption(f"📝 Answered: {session_info['answers_count']}")
        
        # Footer
        st.markdown("---")
        st.info("""
        **SportSync AI v2**
        
        🧠 141 طبقة تحليل
        🎯 8000+ رياضة
        ⚡ AI-Powered
        """)
    
    # ══════════════════════════════════════════════════════════
    # PAGE ROUTING
    # ══════════════════════════════════════════════════════════
    
    page = st.session_state.current_page
    
    if page == 'welcome':
        from pages import welcome
        welcome.show()
    
    elif page == 'questions':
        from pages import questions
        questions.show()
    
    elif page == 'analysis':
        from pages import analysis
        analysis.show()
    
    elif page == 'results':
        from pages import results
        results.show()
    
    else:
        st.error("صفحة غير موجودة!")

if __name__ == "__main__":
    main()
