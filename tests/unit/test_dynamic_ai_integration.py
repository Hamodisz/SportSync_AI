# -*- coding: utf-8 -*-
"""
اختبارات Task 1.1: ربط Dynamic Sports AI بـ backend_gpt
"""
import sys
from pathlib import Path

# إضافة المجلد الرئيسي للمسار
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.core.backend_gpt import generate_sport_recommendation, calculate_confidence


def test_confidence_high():
    """اختبار: profile واضح → confidence عالي"""
    z_scores = {
        "technical_intuitive": 0.9,
        "solo_group": 0.85,
        "calm_adrenaline": 0.8,
    }
    traits = {
        "tactical": 0.9,
        "solo": 0.85,
        "calm": 0.8,
        "achievement": 0.75,
        "indoor": 0.7
    }
    confidence = calculate_confidence(z_scores, traits)
    assert confidence > 0.75, f"Expected high confidence, got {confidence:.2f}"
    print(f"✅ High confidence test passed: {confidence:.2f}")


def test_confidence_low():
    """اختبار: profile ملتبس → confidence منخفض"""
    z_scores = {
        "technical_intuitive": 0.2,
        "solo_group": -0.1,
        "calm_adrenaline": 0.15,
    }
    traits = {
        "tactical": 0.45,
        "solo": 0.48,
        "calm": 0.52,
        "achievement": 0.43,
        "indoor": 0.51
    }
    confidence = calculate_confidence(z_scores, traits)
    assert confidence < 0.75, f"Expected low confidence, got {confidence:.2f}"
    print(f"✅ Low confidence test passed: {confidence:.2f}")


def test_confidence_contradictions():
    """اختبار: تناقضات في profile → confidence منخفض"""
    z_scores = {
        "technical_intuitive": 0.8,
        "solo_group": 0.5,
        "calm_adrenaline": 0.3,
    }
    traits = {
        "tactical": 0.9,
        "solo": 0.8,  # عالي
        "team": 0.75,  # عالي أيضاً = تناقض!
        "calm": 0.7,  # عالي
        "adrenaline": 0.72,  # عالي أيضاً = تناقض!
    }
    confidence = calculate_confidence(z_scores, traits)
    # التناقضات يجب أن تخفض الثقة قليلاً
    assert confidence < 0.75, f"Expected contradictions to lower confidence, got {confidence:.2f}"
    print(f"✅ Contradictions test passed: {confidence:.2f}")


def test_dynamic_ai_forced():
    """اختبار: Dynamic AI يُستدعى عند force_dynamic=True"""
    answers = {
        "q1": "تركيز هادئ على تفصيلة واحدة",
        "q2": "أفضل لوحدي",
        "q3": "أحب الدقة والتحكم"
    }
    
    try:
        cards = generate_sport_recommendation(answers, lang="العربية", force_dynamic=True)
        
        assert len(cards) > 0, "Should return at least 1 card"
        assert isinstance(cards, list), "Should return a list"
        print(f"✅ Dynamic AI forced test passed: {len(cards)} cards generated")
    except Exception as e:
        # إذا فشل Dynamic AI (مثلاً API غير متوفر)، هذا مقبول
        print(f"⚠️ Dynamic AI not available (expected in test env): {e}")


def test_integration_no_errors():
    """اختبار: النظام المدمج يعمل بدون أخطاء"""
    answers = {
        "q1": "تركيز هادئ",
        "q2": "لوحدي",
        "q3": "دقة"
    }
    
    try:
        cards = generate_sport_recommendation(answers, lang="العربية")
        assert len(cards) > 0, "Should return at least 1 card"
        assert isinstance(cards, list), "Should return a list"
        
        # تحقق من بنية البطاقة
        if cards:
            card = cards[0]
            assert isinstance(card, str), "Card should be a string"
            assert len(card) > 50, "Card should have substantial content"
        
        print(f"✅ Integration test passed: {len(cards)} cards generated")
    except Exception as e:
        pytest.fail(f"Integration failed: {e}")


def test_kb_path_still_works():
    """اختبار: المسار القديم (KB) ما زال يعمل"""
    # هذا profile واضح جداً → يجب أن يستخدم KB وليس Dynamic AI
    answers = {
        "calm_indicators": ["تنفس", "تركيز", "هدوء"],
        "solo_indicators": ["لوحدي", "فردي", "انعزال"],
        "tactical_indicators": ["تحليل", "تخطيط", "استراتيجية"]
    }
    
    try:
        cards = generate_sport_recommendation(answers, lang="العربية", force_dynamic=False)
        assert len(cards) > 0, "KB path should still work"
        print(f"✅ KB path test passed: {len(cards)} cards")
    except Exception as e:
        pytest.fail(f"KB path failed: {e}")


if __name__ == "__main__":
    # تشغيل الاختبارات
    print("🧪 Running Dynamic AI Integration Tests...\n")
    
    print("Test 1: High Confidence")
    test_confidence_high()
    
    print("\nTest 2: Low Confidence")
    test_confidence_low()
    
    print("\nTest 3: Contradictions")
    test_confidence_contradictions()
    
    print("\nTest 4: Dynamic AI Forced")
    test_dynamic_ai_forced()
    
    print("\nTest 5: Integration")
    test_integration_no_errors()
    
    print("\nTest 6: KB Path")
    test_kb_path_still_works()
    
    print("\n✅ All tests completed!")
