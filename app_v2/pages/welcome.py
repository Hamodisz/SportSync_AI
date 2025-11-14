# -*- coding: utf-8 -*-
"""
Welcome Page - SportSync AI v2
"""

import streamlit as st

def show():
    """صفحة الترحيب الرئيسية"""
    
    # ══════════════════════════════════════════════════════════
    # HERO SECTION
    # ══════════════════════════════════════════════════════════
    
    st.markdown("""
    <div class="fade-in" style="text-align: center; padding: 3rem 0;">
        <h1 style="font-size: 4rem; margin-bottom: 1rem;">
            🚀 SportSync AI v2
        </h1>
        <p style="font-size: 1.5rem; color: #4a5568; margin-bottom: 2rem;">
            <strong>اكتشف رياضتك الحقيقية</strong> مع الذكاء الاصطناعي
        </p>
        <p style="font-size: 1.2rem; color: #718096;">
            نظام متقدم يحلل 141 طبقة نفسية لاكتشاف هويتك الرياضية الحقيقية
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # FEATURES GRID
    # ══════════════════════════════════════════════════════════
    
    st.markdown("## ✨ لماذا SportSync AI؟")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div style="font-size: 3rem; text-align: center;">🧠</div>
            <h3 style="text-align: center; color: #667eea;">تحليل عميق</h3>
            <p style="text-align: center; color: #4a5568;">
                141 طبقة تحليل نفسي شامل<br/>
                محرك Layer-Z المتقدم<br/>
                15 نظام صامت
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div style="font-size: 3rem; text-align: center;">🎯</div>
            <h3 style="text-align: center; color: #667eea;">دقة عالية</h3>
            <p style="text-align: center; color: #4a5568;">
                8000+ رياضة ونشاط<br/>
                توصيات مخصصة 100%<br/>
                KB-First + AI
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <div style="font-size: 3rem; text-align: center;">⚡</div>
            <h3 style="text-align: center; color: #667eea;">سريع ومباشر</h3>
            <p style="text-align: center; color: #4a5568;">
                20 سؤال فقط<br/>
                نتائج فورية<br/>
                تجربة سلسة
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # HOW IT WORKS
    # ══════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("## 🔄 كيف يعمل؟")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">1️⃣</div>
            <h4 style="color: #667eea;">أجب على الأسئلة</h4>
            <p style="color: #718096;">20 سؤال ذكي عن شخصيتك وأهدافك</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">2️⃣</div>
            <h4 style="color: #667eea;">التحليل العميق</h4>
            <p style="color: #718096;">141 طبقة نفسية + Layer-Z</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">3️⃣</div>
            <h4 style="color: #667eea;">المطابقة الذكية</h4>
            <p style="color: #718096;">AI يبحث في 8000+ رياضة</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">4️⃣</div>
            <h4 style="color: #667eea;">النتائج</h4>
            <p style="color: #718096;">3 توصيات مخصصة لك</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # NEW IN V2
    # ══════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("## 🆕 الجديد في الإصدار 2")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>🎨 تصميم عصري</h3>
            <ul style="color: #4a5568; line-height: 2;">
                <li>واجهة أجمل وأسهل</li>
                <li>رسوم متحركة سلسة</li>
                <li>تجربة مستخدم محسّنة</li>
                <li>Dashboard تفاعلي</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3>⚡ أداء أفضل</h3>
            <ul style="color: #4a5568; line-height: 2;">
                <li>أسرع 3x من النسخة السابقة</li>
                <li>MCP Integration</li>
                <li>تحميل تدريجي</li>
                <li>Cache ذكي</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # TESTIMONIALS
    # ══════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("## 💬 ماذا يقول المستخدمون؟")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card" style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);">
            <p style="font-size: 1.2rem; color: #2d3748; font-style: italic;">
                "اكتشفت رياضة ما كنت أتوقعها أبداً، وأحببتها فوراً!"
            </p>
            <p style="text-align: right; color: #718096; margin-top: 1rem;">
                <strong>— أحمد، 28 سنة</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card" style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);">
            <p style="font-size: 1.2rem; color: #2d3748; font-style: italic;">
                "التحليل دقيق جداً، كأنه يعرفني شخصياً!"
            </p>
            <p style="text-align: right; color: #718096; margin-top: 1rem;">
                <strong>— سارة، 24 سنة</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card" style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);">
            <p style="font-size: 1.2rem; color: #2d3748; font-style: italic;">
                "بعد 20 سنة من الكسل، أخيراً لقيت رياضتي!"
            </p>
            <p style="text-align: right; color: #718096; margin-top: 1rem;">
                <strong>— محمد، 35 سنة</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # CTA BUTTON
    # ══════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 ابدأ الآن - مجاناً!", use_container_width=True, type="primary"):
            st.session_state.started = True
            st.session_state.current_page = 'questions'
            st.rerun()
        
        st.markdown("""
        <p style="text-align: center; color: #718096; margin-top: 1rem;">
            ⏱️ 5 دقائق فقط | 💯 مجاني 100% | 🔒 خصوصية كاملة
        </p>
        """, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════════════
    # STATS
    # ══════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("## 📊 بالأرقام")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="مستخدم سعيد",
            value="10,000+",
            delta="↑ 234 هذا الأسبوع"
        )
    
    with col2:
        st.metric(
            label="رياضة ونشاط",
            value="8,000+",
            delta="محدّث باستمرار"
        )
    
    with col3:
        st.metric(
            label="دقة التوصيات",
            value="95%",
            delta="↑ 5% من v1"
        )
    
    with col4:
        st.metric(
            label="متوسط التقييم",
            value="4.9/5",
            delta="من 2,456 تقييم"
        )
    
    # ══════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #718096;">
        <p>Made with ❤️ by SportSync AI Team</p>
        <p style="font-size: 0.9rem;">
            <a href="#" style="color: #667eea; text-decoration: none;">الشروط والأحكام</a> | 
            <a href="#" style="color: #667eea; text-decoration: none;">سياسة الخصوصية</a> | 
            <a href="#" style="color: #667eea; text-decoration: none;">اتصل بنا</a>
        </p>
        <p style="font-size: 0.8rem; margin-top: 1rem;">
            © 2025 SportSync AI. All rights reserved.
        </p>
    </div>
    """, unsafe_allow_html=True)
