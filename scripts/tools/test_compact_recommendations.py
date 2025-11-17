# -*- coding: utf-8 -*-
"""
Test Compact Recommendations
=============================
اختبار سريع للتوصيات المختصرة
"""

import sys
sys.path.append('/Users/mohammadal-saati/SportSync_AI-1')

from src.core.complete_sport_system import generate_complete_sport_recommendations

# Sample user data
sample_user = {
    "answers": {
        "q1": "أحب التحديات القصيرة",
        "q2": "أكره التكرار",
        "q3": "أحتاج أدرينالين"
    },
    "traits": {
        "openness": 0.8,
        "challenge_seeking": 0.9,
        "novelty_preference": 0.85
    },
    "identity": {
        "explorer": 0.7,
        "warrior": 0.6
    }
}

def test_compact():
    print("\n🧪 Testing Compact Recommendation System...")
    print("=" * 60)
    
    recommendations = generate_complete_sport_recommendations(
        user_answers=sample_user["answers"],
        user_traits=sample_user["traits"],
        user_identity=sample_user["identity"],
        language='ar',
        num_recommendations=3
    )
    
    if not recommendations:
        print("❌ No recommendations generated!")
        return
    
    print(f"\n✅ Generated {len(recommendations)} recommendations\n")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{'='*60}")
        print(f"🎯 Recommendation #{i}")
        print(f"{'='*60}")
        
        # Title
        title = rec.get('enhanced_label') or rec.get('sport_label', 'Unknown')
        print(f"\n**Title:** {title}")
        
        # Description
        desc = rec.get('ai_description', 'No description')
        word_count = len(desc.split())
        status = "✅" if word_count <= 60 else "❌"
        print(f"\n**Description** ({word_count} words {status}):")
        print(f"{desc}")
        
        # Reasons
        reasons = rec.get('ai_reasons', [])
        print(f"\n**Why it suits you** ({len(reasons)} points):")
        for j, reason in enumerate(reasons, 1):
            words = len(reason.split())
            status = "✅" if words <= 12 else "❌"
            print(f"{j}. {reason} ({words} words {status})")
        
        # Score
        score = rec.get('match_score', 0)
        print(f"\n**Match Score:** {score:.1%}")
    
    print(f"\n{'='*60}")
    print("✅ Test completed!")

if __name__ == "__main__":
    test_compact()
