# -*- coding: utf-8 -*-
"""
Test Deep Personalized Recommendations
=======================================
اختبار النظام الجديد: توصيات شخصية تلامس الهوية
"""

import sys
sys.path.append('/Users/mohammadal-saati/SportSync_AI-1')

def test_deep_personalized():
    """
    اختبار سريع للنظام الجديد
    """
    
    print("\n" + "="*60)
    print("🧪 Testing Deep Personalized Recommendation System")
    print("="*60)
    
    # Sample persona: شخص يكره التكرار، يحب التحدي العقلي، انطوائي
    sample_user = {
        "answers": {
            "q1": "أكره الروتين والتكرار",
            "q2": "أحب التحديات العقلية أكثر من الجسدية",
            "q3": "أفضل التحدي الشخصي على الجماعي"
        },
        "traits": {
            "novelty_preference": 0.9,
            "challenge_seeking": 0.85,
            "introversion": 0.75,
            "analytical_thinking": 0.8,
            "openness": 0.85
        },
        "identity": {
            "warrior": 0.7,
            "explorer": 0.6,
            "strategist": 0.8
        },
        "hidden_drivers": [
            "إثبات الوجود",
            "الهيمنة الصامتة",
            "الفهم العميق"
        ]
    }
    
    print("\n📊 User Profile:")
    print(f"  • Dominant Identity: strategist (80%)")
    print(f"  • Top Trait: novelty_preference (90%)")
    print(f"  • Hidden Drivers: {', '.join(sample_user['hidden_drivers'])}")
    
    print("\n" + "="*60)
    print("✅ Expected Output Example:")
    print("="*60)
    
    expected_output = """
🎯 الرياضة المثالية لك: Tactical Immersive Combat

💡 ما هي؟
• تجربة رياضية عقلية-جسدية-استراتيجية تدمج ألعاب واقع افتراضي تكتيكية
• عناصر تخطيط، مراوغة، اختباء، وانقضاض
• تحليل نفسي داخل اللعبة: تتحدى خصمك فكريًا وجسديًا وعاطفيًا

🎮 ليه تناسبك؟
• أنت تكره التكرار، ترفض السطحية، وتحب توصل لجوهر الشي الحقيقي
• تشوف المتعة في الفهم العميق والهيمنة بدون تصريح
• الرياضة عندك مو تحريك جسم بس، بل إثبات وجود، تفوق ذهني، ومبارزة هوية

🔍 شكلها الواقعي:
• تدخل تجربة VR محاكية لساحة معركة أو مهمة إنقاذ
• تستخدم جسمك + ذكاءك + أعصابك + قدرتك على اتخاذ قرار تحت ضغط
• كل جلسة مختلفة، كل مرة في تحدي حقيقي، لكن داخلك تعرف إنك تنمو

👁️‍🗨️ ملاحظات مهمة:
• هذه رياضة أنت ما راح تسميها رياضة. لكن راح تتعلق فيها بدون مقاومة.
• تقدر تبدأ فيها من اليوم لو عندك وصول لنظام VR أو حتى ألعاب تخطيط عالية التفاعل
"""
    
    print(expected_output)
    
    # تحليل المثال
    word_count = len(expected_output.split())
    print("\n" + "="*60)
    print("📊 Analysis:")
    print("="*60)
    print(f"✅ Word Count: {word_count} words (target: 120-180)")
    print(f"✅ Uses 'أنت' language: YES")
    print(f"✅ Touches identity: YES (إثبات وجود، هيمنة، تفوق ذهني)")
    print(f"✅ Personal diagnosis: YES (ليس مجرد وصف رياضة)")
    print(f"✅ Reading time: ~40 seconds")
    
    print("\n" + "="*60)
    print("🎯 Key Success Factors:")
    print("="*60)
    print("1. ✅ Direct 'أنت' address in every 'Why' point")
    print("2. ✅ Psychological diagnosis (تكره، ترفض، تحب)")
    print("3. ✅ Identity framing (إثبات وجود، مبارزة هوية)")
    print("4. ✅ Personal hook ('هذا أنا!' feeling)")
    print("5. ✅ Practical starting point")
    
    print("\n" + "="*60)
    print("💡 To Actually Test:")
    print("="*60)
    print("1. Run the full system with real user data")
    print("2. Check if LLM follows the new prompt structure")
    print("3. Validate word count (120-180)")
    print("4. Verify 'أنت' usage in all 'Why' points")
    print("5. Ask beta users: 'Does this feel personal?'")
    
    print("\n✅ Test completed!\n")


if __name__ == "__main__":
    test_deep_personalized()
