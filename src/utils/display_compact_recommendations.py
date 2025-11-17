# -*- coding: utf-8 -*-
"""
Compact Recommendation Display Template
========================================
قالب عرض التوصيات المختصرة في Streamlit
"""

import streamlit as st

def display_compact_recommendation(rec: dict, index: int):
    """
    عرض توصية واحدة بطريقة مختصرة وجذابة
    
    Args:
        rec: بيانات التوصية
        index: رقم التوصية (1, 2, 3)
    """
    
    # الحصول على البيانات
    title = rec.get('enhanced_label') or rec.get('sport_label', 'رياضة مخصصة')
    description = rec.get('ai_description', 'وصف غير متوفر')
    reasons = rec.get('ai_reasons', [])
    how_to_start = rec.get('how_to_start', [])
    where = rec.get('where_to_play', [])
    
    # Container مع حدود
    with st.container():
        # Header
        if index == 1:
            st.markdown("### 🟢 التوصية رقم 1")
        elif index == 2:
            st.markdown("### 🌿 التوصية رقم 2")
        else:
            st.markdown("### 🔮 التوصية رقم 3 (ابتكارية)")
        
        # Title
        st.markdown(f"## 🎯 {title}")
        
        # Description
        st.markdown("### 💡 ما هي؟")
        st.write(description)
        
        # Why it suits you
        if reasons:
            st.markdown("### 🎮 ليه تناسبك؟")
            for reason in reasons[:3]:  # Max 3
                st.markdown(f"- {reason}")
        
        # How to start
        if how_to_start:
            st.markdown("### 🚀 كيف تبدأ؟")
            for step in how_to_start[:3]:  # Max 3
                st.markdown(f"- {step}")
        
        # Where to play
        if where:
            st.markdown("### 📍 وين تلعب؟")
            for place in where[:3]:  # Max 3
                st.markdown(f"- {place}")
        
        # Rating
        st.markdown("---")
        st.markdown("### ⭐ قيّم هذه التوصية")
        
        # Create 5 columns for star rating
        cols = st.columns(5)
        rating_key = f"rating_{index}"
        
        for i, col in enumerate(cols, 1):
            if col.button(str(i), key=f"{rating_key}_{i}"):
                st.session_state[rating_key] = i
                st.success(f"شكراً! تقييمك: {i}/5 ⭐")
        
        # Separator
        st.markdown("---")


def display_all_recommendations(recommendations: list):
    """
    عرض جميع التوصيات
    """
    
    st.markdown("# 🎯 توصياتك الرياضية")
    st.markdown("**اقرأ كل توصية في 30 ثانية فقط!**")
    st.markdown("---")
    
    for i, rec in enumerate(recommendations, 1):
        display_compact_recommendation(rec, i)
    
    # Footer
    st.markdown("---")
    st.markdown("### 💬 محتاج تفاصيل أكثر؟")
    st.info("اختر رياضة وقيّمها، أو اضغط 'دردش معي' لتسأل عن أي تفاصيل!")
    
    if st.button("🗨️ دردش معي عن الرياضات"):
        st.session_state.show_chat = True


# Example usage for testing
if __name__ == "__main__":
    st.set_page_config(page_title="SportSync AI", page_icon="🎯")
    
    # Sample data
    sample_recommendations = [
        {
            "enhanced_label": "صعود الجدران",
            "ai_description": "تسلق جدران مليئة بالقبضات الملونة. كل مسار لغز جديد يحتاج قوة وذكاء. تصعد خطوة بخطوة حتى تصل للقمة.",
            "ai_reasons": [
                "تحديات قصيرة - كل مسار 2-5 دقائق فقط",
                "لا تكرار - كل جدار مختلف ومثير",
                "أدرينالين ذكي - قوة جسدية + تفكير استراتيجي"
            ],
            "how_to_start": [
                "اليوم 1-2: تعلم القبضات الأساسية والأمان",
                "اليوم 3-5: تقوية الأصابع وتمارين التوازن",
                "اليوم 6-7: أول صعود كامل (مسار سهل)"
            ],
            "where_to_play": [
                "🇸🇦 Rock Climb (الرياض)",
                "🇸🇦 Climb Central (جدة)",
                "🌍 أي Climbing Gym قريب منك"
            ]
        },
        {
            "enhanced_label": "رماية الدقة",
            "ai_description": "تصويب على أهداف بمسافات مختلفة. تركيز كامل، تنفس عميق، ثم إطلاق دقيق. كل هدف تصيبه إنجاز واضح.",
            "ai_reasons": [
                "تحسن مرئي - كل يوم أدق من الأمس",
                "تحدي شخصي - أنت ضد نفسك",
                "إنجاز فوري - النتيجة واضحة ومباشرة"
            ],
            "how_to_start": [
                "اليوم 1-2: تعلم تثبيت النظرة والوقفة",
                "اليوم 3-5: ربط التنفس بالتصويب",
                "اليوم 6-7: أهداف قريبة بدقة 100%"
            ],
            "where_to_play": [
                "🇸🇦 Archery Centers (الرياض/جدة)",
                "🇸🇦 Dart Clubs في المولات",
                "🌍 أي Shooting Range آمن"
            ]
        }
    ]
    
    display_all_recommendations(sample_recommendations)
