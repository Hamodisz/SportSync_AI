# -*- coding: utf-8 -*-
"""
UI Components - SportSync AI v2
"""

import streamlit as st

def show_hero(title, subtitle, description=None):
    """Hero Section"""
    st.markdown(f"""
    <div class="fade-in" style="text-align: center; padding: 3rem 0;">
        <h1 style="font-size: 4rem; margin-bottom: 1rem;">
            {title}
        </h1>
        <p style="font-size: 1.5rem; color: #4a5568; margin-bottom: 1rem;">
            <strong>{subtitle}</strong>
        </p>
        {f'<p style="font-size: 1.2rem; color: #718096;">{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

def show_card(icon, title, content):
    """Feature Card"""
    st.markdown(f"""
    <div class="card">
        <div style="font-size: 3rem; text-align: center;">{icon}</div>
        <h3 style="text-align: center; color: #667eea;">{title}</h3>
        <p style="text-align: center; color: #4a5568;">
            {content}
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_progress_bar(current, total, label=None):
    """Progress Bar"""
    progress = current / total if total > 0 else 0
    percentage = int(progress * 100)
    
    if label:
        st.markdown(f"### {label}")
    
    st.progress(progress)
    st.caption(f"{current}/{total} ({percentage}%)")

def show_metric_card(label, value, delta=None, icon=None):
    """Metric Card"""
    icon_html = f'<span style="font-size: 2rem; margin-right: 0.5rem;">{icon}</span>' if icon else ''
    delta_html = f'<p style="color: #48bb78; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</p>' if delta else ''
    
    st.markdown(f"""
    <div class="card" style="text-align: center;">
        {icon_html}
        <p style="color: #718096; font-size: 0.9rem;">{label}</p>
        <h2 style="color: #667eea; margin: 0.5rem 0;">{value}</h2>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def show_success_message(message):
    """Success Message"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                font-weight: 600;
                text-align: center;">
        ✅ {message}
    </div>
    """, unsafe_allow_html=True)

def show_error_message(message):
    """Error Message"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
                color: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                font-weight: 600;
                text-align: center;">
        ❌ {message}
    </div>
    """, unsafe_allow_html=True)

def show_info_message(message):
    """Info Message"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
                color: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                font-weight: 600;
                text-align: center;">
        ℹ️ {message}
    </div>
    """, unsafe_allow_html=True)

def show_loading(message="جاري التحميل..."):
    """Loading Animation"""
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem 0;">
        <div style="display: inline-block;
                    width: 50px;
                    height: 50px;
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;">
        </div>
        <p style="margin-top: 1rem; color: #718096; font-size: 1.2rem;">
            {message}
        </p>
    </div>
    <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """, unsafe_allow_html=True)

def show_cta_button(text, key, on_click=None):
    """Call to Action Button"""
    if st.button(text, key=key, use_container_width=True, type="primary"):
        if on_click:
            on_click()
        return True
    return False
