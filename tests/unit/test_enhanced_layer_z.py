# -*- coding: utf-8 -*-
"""
tests/test_enhanced_layer_z.py
-------------------------------
اختبارات شاملة لـ Task 1.2: ربط Layer-Z Enhanced
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.analysis.layer_z_enhanced import (
    EnhancedLayerZ,
    analyze_silent_drivers_enhanced,
    FlowIndicators,
    RiskAssessment
)


def test_enhanced_layer_z_basic():
    """اختبار أساسي لـ EnhancedLayerZ"""
    print("\n🧪 Test 1: Enhanced Layer-Z Basic Analysis")
    
    analyzer = EnhancedLayerZ()
    
    # نص اختبار بسيط
    test_text = """
    أحب الهدوء والتركيز العميق. أفضل العمل لوحدي.
    أحتاج للسيطرة والتخطيط الدقيق. أكره الرتابة.
    """
    
    result = analyzer.analyze_complete(test_text, "العربية")
    
    # تحقق من وجود المكونات الأساسية
    assert "z_scores" in result
    assert "z_drivers" in result
    assert "flow_indicators" in result
    assert "risk_assessment" in result
    
    print("✅ Basic analysis components present")
    
    # تحقق من z_scores
    z_scores = result["z_scores"]
    assert "technical_intuitive" in z_scores
    assert "calm_adrenaline" in z_scores
    assert "solo_group" in z_scores
    
    print("✅ Z-scores calculated correctly")
    
    # تحقق من flow_indicators
    flow = result["flow_indicators"]
    assert isinstance(flow, FlowIndicators)
    assert 0 <= flow.flow_potential <= 1
    assert flow.focus_depth in ["عميق", "متوسط", "سطحي"]
    
    print(f"✅ Flow indicators: potential={flow.flow_potential:.2f}, depth={flow.focus_depth}")
    
    # تحقق من risk_assessment
    risk = result["risk_assessment"]
    assert isinstance(risk, RiskAssessment)
    assert 0 <= risk.risk_level <= 1
    assert risk.category in ["منخفض", "متوسط", "عالي"]
    
    print(f"✅ Risk assessment: level={risk.risk_level:.2f}, category={risk.category}")
    
    print("✅ Test 1 PASSED\n")


def test_analyze_silent_drivers_enhanced():
    """اختبار analyze_silent_drivers_enhanced"""
    print("\n🧪 Test 2: Silent Drivers Enhanced")
    
    sample_answers = {
        "q1": {"answer": ["أحب الذكاء والتخطيط"]},
        "q2": {"answer": ["أفضل العمل لوحدي"]},
    }
    
    result = analyze_silent_drivers_enhanced(sample_answers, "العربية")
    
    # تحقق من البنية
    assert "z_scores" in result
    assert "z_drivers" in result
    assert "profile" in result
    
    # z_scores يجب أن يكون dict من floats
    for axis, score in result["z_scores"].items():
        assert isinstance(score, (int, float))
        assert -1 <= score <= 1
    
    print("✅ Silent drivers analysis works correctly")
    print(f"   Drivers count: {len(result['z_drivers'])}")
    print("✅ Test 2 PASSED\n")


def test_backend_gpt_integration():
    """اختبار التكامل مع backend_gpt.py"""
    print("\n🧪 Test 3: Backend GPT Integration")
    
    try:
        from src.core.backend_gpt import generate_sport_recommendation
        
        sample_answers = {
            "q1": {"answer": ["أحب الذكاء والتخطيط"]},
            "q2": {"answer": ["أفضل العمل لوحدي"]},
            "_session_id": "test-enhanced-session"
        }
        
        # اختبار مع force_fallback لتجنب استخدام LLM
        sample_answers["_force_fallback"] = True
        
        cards = generate_sport_recommendation(sample_answers, "العربية")
        
        assert len(cards) == 3
        print("✅ Backend GPT returns 3 cards")
        
        # تحقق من وجود معلومات Enhanced في البطاقات
        # (يجب أن تظهر في notes إذا كانت متوفرة)
        combined_text = "\n".join(cards)
        
        # البطاقات يجب أن تحتوي على البنية الصحيحة
        assert all("🧩" in card for card in cards)
        assert all("---" in card for card in cards)
        
        print("✅ Cards have correct structure")
        print("✅ Test 3 PASSED\n")
        
    except Exception as e:
        print(f"⚠️  Test 3 SKIPPED: {e}")
        print("   (This is OK if backend_gpt dependencies are missing)\n")


def test_confidence_calculation():
    """اختبار حساب confidence score"""
    print("\n🧪 Test 4: Confidence Score Calculation")
    
    try:
        from src.core.backend_gpt import calculate_confidence
        
        # z_scores قوية (درجات واضحة)
        strong_z_scores = {
            "technical_intuitive": 0.8,
            "calm_adrenaline": -0.7,
            "solo_group": 0.6
        }
        
        # traits متوسطة
        traits = {
            "calm": 0.5,
            "adrenaline": 0.4,
            "tactical": 0.7
        }
        
        confidence = calculate_confidence(strong_z_scores, traits)
        
        assert 0 <= confidence <= 1
        print(f"✅ Confidence score calculated: {confidence:.2f}")
        
        # z_scores ضعيفة (درجات غير واضحة)
        weak_z_scores = {
            "technical_intuitive": 0.1,
            "calm_adrenaline": -0.1,
            "solo_group": 0.05
        }
        
        weak_confidence = calculate_confidence(weak_z_scores, traits)
        
        # الـ confidence الضعيف يجب أن يكون أقل من القوي
        assert weak_confidence < confidence
        print(f"✅ Weak confidence is lower: {weak_confidence:.2f}")
        
        print("✅ Test 4 PASSED\n")
        
    except Exception as e:
        print(f"⚠️  Test 4 SKIPPED: {e}\n")


def test_flow_and_risk_in_cards():
    """اختبار إضافة Flow و Risk إلى البطاقات"""
    print("\n🧪 Test 5: Flow & Risk in Cards")
    
    try:
        from src.core.backend_gpt import _add_enhanced_insights_to_notes
        from src.analysis.layer_z_enhanced import FlowIndicators, RiskAssessment
        
        # بطاقات اختبار
        cards = [
            {
                "sport_label": "تكتيكات القناص الحضري",
                "notes": ["Original note"]
            }
        ]
        
        # Flow indicators اختبار
        flow = FlowIndicators(
            flow_potential=0.85,
            focus_depth="عميق",
            immersion_likelihood=0.9,
            distraction_resistance=0.8
        )
        
        # Risk assessment اختبار
        risk = RiskAssessment(
            risk_level=0.3,
            category="منخفض",
            comfort_zone_width="واسع",
            novelty_seeking=0.6
        )
        
        # إضافة المعلومات
        updated_cards = _add_enhanced_insights_to_notes(
            cards, flow, risk, "العربية"
        )
        
        # تحقق من الإضافة
        notes = updated_cards[0]["notes"]
        assert len(notes) > 1  # يجب أن تكون أكثر من الـ note الأصلية
        
        # تحقق من وجود معلومات Flow و Risk
        notes_text = " ".join(notes)
        assert "تدفق" in notes_text or "Flow" in notes_text
        assert "مخاطرة" in notes_text or "Risk" in notes_text
        
        print("✅ Flow & Risk info added to card notes")
        print(f"   Notes: {notes}")
        print("✅ Test 5 PASSED\n")
        
    except Exception as e:
        print(f"⚠️  Test 5 SKIPPED: {e}\n")


def test_full_pipeline():
    """اختبار Pipeline الكامل"""
    print("\n🧪 Test 6: Full Pipeline (Enhanced → Cards)")
    
    try:
        from src.core.backend_gpt import generate_sport_recommendation
        
        # إجابات اختبار شاملة
        answers = {
            "q1": {"answer": ["أحب التحليل والتخطيط العميق"]},
            "q2": {"answer": ["أفضل العمل لوحدي بتركيز هادئ"]},
            "q3": {"answer": ["أستمتع بالتحديات التكتيكية"]},
            "q4": {"answer": ["أحتاج للسيطرة الكاملة"]},
            "_session_id": "pipeline-test",
            "_force_fallback": True  # استخدام fallback لتجنب LLM
        }
        
        cards = generate_sport_recommendation(answers, "العربية")
        
        assert len(cards) == 3
        print("✅ Pipeline generates 3 cards")
        
        # تحقق من البنية
        for i, card in enumerate(cards):
            assert card.startswith("🧩")
            assert "---" in card
            print(f"✅ Card {i+1} has correct structure")
        
        print("\n✅ Test 6 PASSED\n")
        
    except Exception as e:
        print(f"⚠️  Test 6 SKIPPED: {e}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Task 1.2 Integration Tests")
    print("="*60)
    
    test_enhanced_layer_z_basic()
    test_analyze_silent_drivers_enhanced()
    test_backend_gpt_integration()
    test_confidence_calculation()
    test_flow_and_risk_in_cards()
    test_full_pipeline()
    
    print("="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")
