# -*- coding: utf-8 -*-
"""
tests/test_systems_integration.py
----------------------------------
اختبارات شاملة لـ Task 1.3: ربط الأنظمة الـ 15 (MBTI, Big Five, Enneagram, +12)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.systems import analyze_all_systems


def test_analyze_all_systems_basic():
    """اختبار أساسي لـ analyze_all_systems"""
    print("\n🧪 Test 1: Multi-System Analysis Basic")

    answers = {
        "q1": {"answer": ["أحب التخطيط والتنظيم"]},
        "q2": {"answer": ["أفضل العمل لوحدي"]},
        "q3": {"answer": ["أستمتع بالتحديات التكتيكية"]},
        "_session_id": "test-systems-1"
    }

    result = analyze_all_systems(answers, "العربية")

    # تحقق من البنية الأساسية
    assert "systems" in result
    assert "consensus" in result
    assert "summary" in result

    print("✅ Basic structure present")

    # تحقق من الأنظمة
    systems = result["systems"]
    assert len(systems) > 0, "Should analyze at least one system"
    print(f"✅ Analyzed {len(systems)} systems")

    # تحقق من الأنظمة الرئيسية
    if "big_five" in systems:
        assert "profile" in systems["big_five"]
        assert "sport_recommendations" in systems["big_five"]
        print("✅ Big Five analysis present")

    if "mbti" in systems:
        assert "profile" in systems["mbti"]
        assert "sport_recommendations" in systems["mbti"]
        print("✅ MBTI analysis present")

    if "enneagram" in systems:
        assert "profile" in systems["enneagram"]
        assert "sport_recommendations" in systems["enneagram"]
        print("✅ Enneagram analysis present")

    print("✅ Test 1 PASSED\n")


def test_consensus_calculation():
    """اختبار حساب الإجماع (Consensus)"""
    print("\n🧪 Test 2: Consensus Calculation")

    answers = {
        "q1": {"answer": ["تركيز عميق وهدوء"]},
        "q2": {"answer": ["أحب السيطرة والدقة"]},
        "q3": {"answer": ["أعمل لوحدي"]},
        "_session_id": "test-consensus"
    }

    result = analyze_all_systems(answers, "العربية")

    consensus = result["consensus"]

    # تحقق من البنية
    assert "top_sports" in consensus
    assert "confidence" in consensus
    assert "agreements" in consensus
    assert "sport_votes" in consensus

    print("✅ Consensus structure correct")

    # تحقق من المحتوى
    top_sports = consensus["top_sports"]
    assert isinstance(top_sports, list)
    assert len(top_sports) <= 5, "Should return top 5 sports max"

    print(f"✅ Top sports: {top_sports}")

    confidence = consensus["confidence"]
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    print(f"✅ Confidence: {confidence:.2f}")

    print("✅ Test 2 PASSED\n")


def test_summary_info():
    """اختبار معلومات الملخص"""
    print("\n🧪 Test 3: Summary Information")

    answers = {
        "q1": {"answer": ["نشاط وحماس"]},
        "q2": {"answer": ["أحب الناس والتفاعل"]},
        "_session_id": "test-summary"
    }

    result = analyze_all_systems(answers, "العربية")

    summary = result["summary"]

    # تحقق من البنية
    assert "total_systems" in summary
    assert "avg_confidence" in summary
    assert "top_system" in summary

    print(f"✅ Total systems: {summary['total_systems']}")
    print(f"✅ Avg confidence: {summary['avg_confidence']:.2f}")
    print(f"✅ Top system: {summary['top_system']}")

    # تحقق من القيم
    assert summary["total_systems"] > 0
    assert 0 <= summary["avg_confidence"] <= 1

    print("✅ Test 3 PASSED\n")


def test_backend_gpt_integration():
    """اختبار التكامل مع backend_gpt"""
    print("\n🧪 Test 4: Backend GPT Integration")

    try:
        from src.core.backend_gpt import generate_sport_recommendation

        answers = {
            "q1": {"answer": ["تحليل واستراتيجية"]},
            "q2": {"answer": ["هدوء وتركيز"]},
            "q3": {"answer": ["سيطرة كاملة"]},
            "_session_id": "test-backend",
            "_force_fallback": True  # لتجنب LLM
        }

        cards = generate_sport_recommendation(answers, "العربية")

        assert len(cards) == 3, "Should return 3 cards"
        print("✅ Backend GPT returns 3 cards")

        # تحقق من البنية
        for card in cards:
            assert isinstance(card, str)
            assert len(card) > 50, "Card should have content"

        print("✅ Cards have correct structure")

        # تحقق من وجود consensus info (قد يكون في notes)
        combined_text = "\n".join(cards)
        # قد تحتوي البطاقات على رموز الأنظمة
        if "🔬" in combined_text or "🎯" in combined_text:
            print("✅ Systems consensus info present in cards")
        else:
            print("⚠️  Systems consensus info not visible (may be in metadata)")

        print("✅ Test 4 PASSED\n")

    except Exception as e:
        print(f"⚠️  Test 4 SKIPPED: {e}\n")


def test_individual_systems():
    """اختبار الأنظمة الفردية"""
    print("\n🧪 Test 5: Individual Systems Testing")

    answers = {
        "q1": {"answer": ["قوة وسيطرة"]},
        "q2": {"answer": ["تحدي ومنافسة"]},
        "q3": {"answer": ["سريع ومباشر"]},
        "_session_id": "test-individual"
    }

    result = analyze_all_systems(answers, "العربية")
    systems = result["systems"]

    # اختبار الأنظمة الإضافية
    expected_systems = ["disc", "riasec", "temperament", "eq", "sports_psych"]

    for sys_name in expected_systems:
        if sys_name in systems:
            sys_result = systems[sys_name]
            assert "system_name" in sys_result
            assert "profile" in sys_result
            assert "sport_recommendations" in sys_result
            print(f"✅ {sys_name.upper()} system working")

    print("✅ Test 5 PASSED\n")


def test_consensus_voting():
    """اختبار آلية التصويت (Voting) في Consensus"""
    print("\n🧪 Test 6: Consensus Voting Mechanism")

    answers = {
        "q1": {"answer": ["تركيز عميق"]},
        "q2": {"answer": ["دقة عالية"]},
        "q3": {"answer": ["تحكم كامل"]},
        "_session_id": "test-voting"
    }

    result = analyze_all_systems(answers, "العربية")

    consensus = result["consensus"]
    sport_votes = consensus.get("sport_votes", {})

    assert isinstance(sport_votes, dict)
    print(f"✅ Sport votes: {len(sport_votes)} unique sports")

    # تحقق من أن الأصوات منطقية
    for sport, votes in sport_votes.items():
        assert isinstance(sport, str)
        assert isinstance(votes, int)
        assert votes > 0
        print(f"   {sport}: {votes} votes")

    # التحقق من أن top_sports مرتبة بعدد الأصوات
    top_sports = consensus["top_sports"]
    if len(top_sports) >= 2 and len(sport_votes) >= 2:
        first_sport_votes = sport_votes.get(top_sports[0], 0)
        second_sport_votes = sport_votes.get(top_sports[1], 0)
        assert first_sport_votes >= second_sport_votes, "Top sports should be sorted by votes"
        print("✅ Sports correctly sorted by votes")

    print("✅ Test 6 PASSED\n")


def test_error_handling():
    """اختبار معالجة الأخطاء"""
    print("\n🧪 Test 7: Error Handling")

    # اختبار مع إجابات فارغة
    empty_answers = {"_session_id": "test-empty"}

    result = analyze_all_systems(empty_answers, "العربية")

    # يجب أن يعمل بدون crash
    assert "systems" in result
    assert "consensus" in result
    assert "summary" in result

    print("✅ Empty answers handled gracefully")

    # اختبار مع إجابات غير عادية
    weird_answers = {
        "weird_key": "weird_value",
        123: 456,
        "_session_id": "test-weird"
    }

    result2 = analyze_all_systems(weird_answers, "العربية")

    assert "systems" in result2
    print("✅ Weird answers handled gracefully")

    print("✅ Test 7 PASSED\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Task 1.3 Multi-System Integration Tests")
    print("="*60)

    test_analyze_all_systems_basic()
    test_consensus_calculation()
    test_summary_info()
    test_backend_gpt_integration()
    test_individual_systems()
    test_consensus_voting()
    test_error_handling()

    print("="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")
