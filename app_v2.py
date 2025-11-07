#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SportSync AI - User-Friendly Chat Interface
===========================================
Triple Intelligence System with Streaming Display
"""

import streamlit as st
import json
import time
from typing import Generator
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.ai_orchestrator import generate_sport_recommendations

# Page config
st.set_page_config(
    page_title="SportSync AI - مكتشف الرياضة المثالية",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS for better UX
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-header {
        text-align: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        animation: fadeIn 0.5s;
    }
    .user-message {
        background: rgba(255, 255, 255, 0.9);
        margin-left: 20%;
    }
    .ai-message {
        background: rgba(103, 126, 234, 0.2);
        margin-right: 20%;
        color: white;
    }
    .layer-indicator {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.2rem;
    }
    .layer-fast { background: #10b981; color: white; }
    .layer-reasoning { background: #f59e0b; color: white; }
    .layer-intelligence { background: #8b5cf6; color: white; }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'pipeline_status' not in st.session_state:
    st.session_state.pipeline_status = None


def display_layer_status(layer: str, status: str):
    """Display layer processing status"""
    colors = {
        "fast": "🚀",
        "reasoning": "🧠", 
        "intelligence": "🎯"
    }
    icon = colors.get(layer, "⚙️")
    
    if status == "processing":
        return f"{icon} **{layer.upper()}** يعمل الآن..."
    elif status == "complete":
        return f"✅ **{layer.upper()}** اكتمل"
    elif status == "failed":
        return f"❌ **{layer.upper()}** فشل"


def stream_text(text: str, delay: float = 0.02) -> Generator[str, None, None]:
    """Stream text character by character for better UX"""
    for char in text:
        yield char
        time.sleep(delay)


def format_recommendation(rec: dict, index: int) -> str:
    """Format a single recommendation beautifully"""
    icons = ["🟢", "🌿", "🔮"]
    icon = icons[index] if index < 3 else "⭐"
    
    markdown = f"""
### {icon} التوصية رقم {index + 1}: {rec.get('title', 'رياضة مبتكرة')}

**✨ الجوهر:**
{rec.get('essence', 'تجربة فريدة')}

**💫 التجربة:**
{rec.get('experience', 'وصف التجربة')}

**🎯 لماذا مثالية لك:**
"""
    
    for reason in rec.get('why_perfect', []):
        markdown += f"\n- {reason}"
    
    markdown += f"\n\n**🚀 الأسبوع الأول:**\n{rec.get('first_week', 'ابدأ بخطوات صغيرة')}"
    
    markdown += "\n\n**✅ علامات التقدم:**"
    for sign in rec.get('signs_of_progress', []):
        markdown += f"\n- {sign}"
    
    return markdown


# Header
st.markdown("""
<div class="main-header">
    <h1 style="color: white; font-size: 3rem; margin: 0;">🧠 نظام الذكاء الثلاثي</h1>
    <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem;">
        Fast → Reasoning → Intelligence | لا يوجد Fallback ✗
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar with system info
with st.sidebar:
    st.markdown("### ⚙️ معلومات النظام")
    
    st.markdown("""
    **الطبقات الثلاث:**
    - 🚀 **Fast**: GPT-3.5-turbo (استخلاص سريع)
    - 🧠 **Reasoning**: o1-mini (تحليل عميق)
    - 🎯 **Intelligence**: GPT-4 (توصيات نهائية)
    """)
    
    st.markdown("---")
    
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.session_state.pipeline_status = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("**📊 الإحصائيات:**")
    st.write(f"عدد الرسائل: {len(st.session_state.messages)}")

# Chat interface
st.markdown("### 💬 المحادثة")

# Display chat history
for message in st.session_state.messages:
    css_class = "user-message" if message["role"] == "user" else "ai-message"
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{"🧑 أنت" if message["role"] == "user" else "🤖 SportSync AI"}:</strong><br>
        {message["content"]}
    </div>
    """, unsafe_allow_html=True)

# User input
user_input = st.chat_input("اكتب وصفاً لما تبحث عنه في رياضة...")

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message immediately
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>🧑 أنت:</strong><br>
        {user_input}
    </div>
    """, unsafe_allow_html=True)
    
    # Create placeholder for AI response
    response_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Show processing status
    with status_placeholder.container():
        st.markdown("### ⚙️ جاري التحليل...")
        
        layer_status_fast = st.empty()
        layer_status_reasoning = st.empty()
        layer_status_intelligence = st.empty()
        
        layer_status_fast.markdown(display_layer_status("fast", "processing"))
    
    # Generate recommendations
    try:
        result = generate_sport_recommendations(user_input, "ar")
        
        if not result["success"]:
            # Show error
            error_msg = "❌ **فشل النظام!**\n\n"
            error_msg += "\n".join(f"- {err}" for err in result["errors"])
            
            response_placeholder.markdown(f"""
            <div class="chat-message ai-message">
                <strong>🤖 SportSync AI:</strong><br>
                {error_msg}
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })
            
        else:
            # Update status for each layer
            layer_status_fast.markdown(display_layer_status("fast", "complete"))
            layer_status_reasoning.markdown(display_layer_status("reasoning", "processing"))
            time.sleep(0.5)
            
            layer_status_reasoning.markdown(display_layer_status("reasoning", "complete"))
            layer_status_intelligence.markdown(display_layer_status("intelligence", "processing"))
            time.sleep(0.5)
            
            layer_status_intelligence.markdown(display_layer_status("intelligence", "complete"))
            
            # Clear status, show recommendations
            status_placeholder.empty()
            
            # Parse recommendations
            try:
                recs_data = json.loads(result["final_recommendations"])
                recommendations = recs_data.get("recommendations", [])
                
                if not recommendations:
                    raise ValueError("No recommendations found")
                
                # Build response with streaming effect
                full_response = "✅ **تم إنشاء التوصيات بنجاح!**\n\n"
                full_response += f"📊 **استخدام النماذج**: {result['total_tokens']} token\n\n"
                full_response += "---\n\n"
                
                for i, rec in enumerate(recommendations[:3]):
                    full_response += format_recommendation(rec, i)
                    full_response += "\n\n---\n\n"
                
                # Display with streaming effect
                response_text = ""
                response_container = response_placeholder.container()
                
                with response_container:
                    text_placeholder = st.empty()
                    
                    # Stream the text
                    for char in full_response:
                        response_text += char
                        text_placeholder.markdown(f"""
                        <div class="chat-message ai-message">
                            <strong>🤖 SportSync AI:</strong><br>
                            {response_text}
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.01)  # Adjust speed here
                
                # Save to session
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
                
            except json.JSONDecodeError:
                error_msg = "❌ خطأ في تحليل النتائج. الرجاء المحاولة مرة أخرى."
                response_placeholder.markdown(f"""
                <div class="chat-message ai-message">
                    <strong>🤖 SportSync AI:</strong><br>
                    {error_msg}
                </div>
                """, unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
    
    except Exception as e:
        error_msg = f"❌ **حدث خطأ غير متوقع:**\n\n{str(e)}"
        response_placeholder.markdown(f"""
        <div class="chat-message ai-message">
            <strong>🤖 SportSync AI:</strong><br>
            {error_msg}
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": error_msg
        })

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.7); padding: 1rem;">
    <p>SportSync AI - نظام الذكاء الثلاثي المتكامل</p>
    <p style="font-size: 0.8rem;">Powered by OpenAI GPT-3.5, o1-mini, and GPT-4</p>
</div>
""", unsafe_allow_html=True)


# Quick start examples
if len(st.session_state.messages) == 0:
    st.markdown("### 💡 جرب هذه الأمثلة:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧘 أريد شيئاً هادئاً"):
            st.session_state.messages.append({
                "role": "user",
                "content": "أبحث عن رياضة هادئة تساعدني على التركيز والاسترخاء"
            })
            st.rerun()
    
    with col2:
        if st.button("🎯 أحب التحديات العقلية"):
            st.session_state.messages.append({
                "role": "user",
                "content": "أريد رياضة تجمع بين التفكير الاستراتيجي والحركة البدنية"
            })
            st.rerun()
    
    with col3:
        if st.button("👥 أفضل الجماعية"):
            st.session_state.messages.append({
                "role": "user",
                "content": "أبحث عن رياضة جماعية ممتعة تساعدني على بناء صداقات"
            })
            st.rerun()
