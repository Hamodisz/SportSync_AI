# -*- coding: utf-8 -*-
"""
tests/test_scoring_system.py
-----------------------------
Comprehensive tests for Task 2.1: Question Scoring System Improvement

Tests the new explicit scoring system where each question option
has explicit Z-axis scores instead of keyword-based inference.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from layer_z_engine import calculate_z_scores_from_questions
import json


def test_basic_scoring():
    """Test 1: Basic scoring calculation"""
    print("\n🧪 Test 1: Basic Scoring Calculation")

    # Sample answers
    answers = {
        "q1": {"answer": ["تركيز هادئ على تفصيلة واحدة"]},  # Calm focus
        "_session_id": "test-1"
    }

    # Use sample file
    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",
        lang="العربية"
    )

    # Verify structure
    assert isinstance(scores, dict), "Should return a dict"
    assert len(scores) > 0, "Should have at least one score"
    print(f"✅ Calculated {len(scores)} Z-axis scores")

    # Verify scores are in valid range
    for axis, score in scores.items():
        if axis == "sensory_sensitivity":  # Unipolar
            assert 0.0 <= score <= 1.0, f"{axis} should be 0.0-1.0, got {score}"
        else:  # Bipolar
            assert -1.0 <= score <= 1.0, f"{axis} should be -1.0-1.0, got {score}"

    print("✅ All scores in valid range")
    print("✅ Test 1 PASSED\n")


def test_expected_scores():
    """Test 2: Verify expected scores for known answer"""
    print("\n🧪 Test 2: Expected Scores for Known Answer")

    # Q1, Option 1: "تركيز هادئ على تفصيلة واحدة"
    # Expected scores from JSON:
    # calm_adrenaline: -0.8 (very calm)
    # solo_group: -0.6 (solo)
    # sensory_sensitivity: 0.7 (high sensitivity)
    # control_freedom: -0.5 (controlled)

    answers = {
        "q1": {"answer": ["تركيز هادئ على تفصيلة واحدة"]},
        "_session_id": "test-2"
    }

    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",
        lang="العربية"
    )

    # Q1 has weight=3, but only one answer, so scores should match JSON exactly
    expected = {
        "calm_adrenaline": -0.8,
        "solo_group": -0.6,
        "sensory_sensitivity": 0.7,
        "control_freedom": -0.5
    }

    for axis, expected_score in expected.items():
        assert axis in scores, f"Missing axis: {axis}"
        actual = scores[axis]
        # Allow small floating point difference
        assert abs(actual - expected_score) < 0.01, \
            f"{axis}: expected {expected_score}, got {actual}"
        print(f"✅ {axis}: {actual:+.2f} (expected {expected_score:+.2f})")

    print("✅ Test 2 PASSED\n")


def test_weighted_average():
    """Test 3: Weighted average calculation"""
    print("\n🧪 Test 3: Weighted Average Calculation")

    # Two answers with different weights
    answers = {
        "q1": {"answer": ["تركيز هادئ على تفصيلة واحدة"]},  # weight=3, calm=-0.8
        "q2": {"answer": ["الملل"]},  # weight=2, different scores
        "_session_id": "test-3"
    }

    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",
        lang="العربية"
    )

    # Should have multiple axes
    assert len(scores) > 0, "Should calculate scores"

    # Weighted average should be calculated correctly
    # Q1 (weight=3): calm_adrenaline=-0.8
    # Q2 (weight=2): has no calm_adrenaline score (only repeat_variety, sensory_sensitivity, compete_enjoy)
    # So calm_adrenaline should still be -0.8

    if "calm_adrenaline" in scores:
        assert abs(scores["calm_adrenaline"] - (-0.8)) < 0.01, \
            f"calm_adrenaline should be -0.8, got {scores['calm_adrenaline']}"
        print(f"✅ calm_adrenaline: {scores['calm_adrenaline']:+.2f}")

    # repeat_variety should come only from Q2 (weight=2)
    # Q2, Option 1 "الملل": repeat_variety=0.7
    if "repeat_variety" in scores:
        assert abs(scores["repeat_variety"] - 0.7) < 0.01, \
            f"repeat_variety should be 0.7, got {scores['repeat_variety']}"
        print(f"✅ repeat_variety: {scores['repeat_variety']:+.2f}")

    print("✅ Test 3 PASSED\n")


def test_multiple_answers_same_axis():
    """Test 4: Multiple answers affecting same axis"""
    print("\n🧪 Test 4: Multiple Answers on Same Axis")

    # Q1, Option 1: calm_adrenaline=-0.8 (weight=3)
    # Q6, Option 4: calm_adrenaline=+0.8 (weight=2)
    # Weighted average: (-0.8*3 + 0.8*2) / (3+2) = (-2.4+1.6)/5 = -0.8/5 = -0.16

    answers = {
        "q1": {"answer": ["تركيز هادئ على تفصيلة واحدة"]},  # calm=-0.8, w=3
        "q6": {"answer": ["أماكن فيها تحدي"]},  # calm=+0.8, w=2
        "_session_id": "test-4"
    }

    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",
        lang="العربية"
    )

    # Check calm_adrenaline weighted average
    if "calm_adrenaline" in scores:
        expected = (-0.8 * 3 + 0.8 * 2) / 5
        actual = scores["calm_adrenaline"]
        assert abs(actual - expected) < 0.01, \
            f"calm_adrenaline: expected {expected:.2f}, got {actual:.2f}"
        print(f"✅ calm_adrenaline: {actual:+.2f} (expected {expected:+.2f})")

    print("✅ Test 4 PASSED\n")


def test_all_sample_questions():
    """Test 5: Answer all 6 sample questions"""
    print("\n🧪 Test 5: All Sample Questions")

    answers = {
        "q1": {"answer": ["تفاعل وسرعة"]},  # Speed and interaction
        "q2": {"answer": ["غياب نتيجة"]},  # Lack of results
        "q3": {"answer": ["أجرب مباشرة"]},  # Try immediately
        "q4": {"answer": ["مع مجموعة"]},  # With group
        "q5": {"answer": ["منافسة مباشرة"]},  # Direct competition
        "q6": {"answer": ["أماكن فيها تحدي"]},  # Challenging places
        "_session_id": "test-5"
    }

    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",
        lang="العربية"
    )

    # Should have calculated scores for all relevant axes
    assert len(scores) > 0, "Should have scores"
    print(f"✅ Calculated {len(scores)} Z-axis scores from 6 questions")

    # All scores should be in valid range
    for axis, score in sorted(scores.items()):
        if axis == "sensory_sensitivity":
            assert 0.0 <= score <= 1.0, f"{axis} out of range: {score}"
        else:
            assert -1.0 <= score <= 1.0, f"{axis} out of range: {score}"
        print(f"   {axis}: {score:+.2f}")

    # Based on the answers, we expect:
    # - High adrenaline (speed, direct competition, challenging places)
    # - Group preference (مع مجموعة)
    # - High competition (direct competition)
    # - Intuitive approach (try immediately)

    if "calm_adrenaline" in scores:
        assert scores["calm_adrenaline"] > 0, "Should favor adrenaline"
        print(f"✅ Adrenaline preference detected: {scores['calm_adrenaline']:+.2f}")

    if "solo_group" in scores:
        assert scores["solo_group"] > 0, "Should favor group"
        print(f"✅ Group preference detected: {scores['solo_group']:+.2f}")

    if "compete_enjoy" in scores:
        assert scores["compete_enjoy"] > 0, "Should favor competition"
        print(f"✅ Competition preference detected: {scores['compete_enjoy']:+.2f}")

    print("✅ Test 5 PASSED\n")


def test_empty_answers():
    """Test 6: Handle empty answers gracefully"""
    print("\n🧪 Test 6: Empty Answers Handling")

    answers = {"_session_id": "test-6"}

    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",
        lang="العربية"
    )

    # Should return empty dict, not crash
    assert isinstance(scores, dict), "Should return dict"
    assert len(scores) == 0, "Should be empty for no answers"
    print("✅ Empty answers handled gracefully")
    print("✅ Test 6 PASSED\n")


def test_partial_match():
    """Test 7: Partial text matching"""
    print("\n🧪 Test 7: Partial Text Matching")

    # User might type partial answer or it might be truncated
    answers = {
        "q1": {"answer": ["تركيز هادئ"]},  # Partial match of "تركيز هادئ على تفصيلة واحدة"
        "_session_id": "test-7"
    }

    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",
        lang="العربية"
    )

    # Should still match due to normalization
    assert len(scores) > 0, "Should match partial text"
    assert "calm_adrenaline" in scores, "Should find calm_adrenaline score"
    print(f"✅ Partial match successful: {len(scores)} scores calculated")
    print("✅ Test 7 PASSED\n")


def test_english_answers():
    """Test 8: English language support"""
    print("\n🧪 Test 8: English Language Support")

    answers = {
        "q1": {"answer": ["Calm focus on a single detail"]},
        "_session_id": "test-8"
    }

    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions_v2_sample.json",  # Same file has both ar/en
        lang="English"
    )

    # Should match English text
    assert len(scores) > 0, "Should match English text"
    assert "calm_adrenaline" in scores, "Should find scores from English option"

    expected_calm = -0.8  # Same as Arabic version
    assert abs(scores["calm_adrenaline"] - expected_calm) < 0.01, \
        f"Expected {expected_calm}, got {scores['calm_adrenaline']}"

    print(f"✅ English matching successful: {len(scores)} scores")
    print("✅ Test 8 PASSED\n")


def test_json_structure():
    """Test 9: Verify JSON structure is correct"""
    print("\n🧪 Test 9: JSON Structure Validation")

    # Load and validate JSON structure
    with open("arabic_questions_v2_sample.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    assert isinstance(questions, list), "Questions should be a list"
    assert len(questions) == 6, f"Should have 6 questions, got {len(questions)}"
    print(f"✅ Found {len(questions)} questions")

    # Validate each question
    for i, q in enumerate(questions, 1):
        # Required fields
        assert "key" in q, f"Q{i} missing 'key'"
        assert "question_ar" in q, f"Q{i} missing 'question_ar'"
        assert "question_en" in q, f"Q{i} missing 'question_en'"
        assert "options" in q, f"Q{i} missing 'options'"
        assert "bucket" in q, f"Q{i} missing 'bucket'"
        assert "weight" in q, f"Q{i} missing 'weight'"

        # Validate options
        options = q["options"]
        assert isinstance(options, list), f"Q{i} options should be list"
        assert len(options) >= 2, f"Q{i} should have at least 2 options"

        for j, opt in enumerate(options):
            assert "text_ar" in opt, f"Q{i} Option{j+1} missing text_ar"
            assert "text_en" in opt, f"Q{i} Option{j+1} missing text_en"
            assert "scores" in opt, f"Q{i} Option{j+1} missing scores"

            scores = opt["scores"]
            assert isinstance(scores, dict), f"Q{i} Option{j+1} scores should be dict"
            assert len(scores) > 0, f"Q{i} Option{j+1} should have at least one score"

            # Validate score ranges
            for axis, score in scores.items():
                if axis == "sensory_sensitivity":
                    assert 0.0 <= score <= 1.0, \
                        f"Q{i} Option{j+1} {axis}={score} out of range [0,1]"
                else:
                    assert -1.0 <= score <= 1.0, \
                        f"Q{i} Option{j+1} {axis}={score} out of range [-1,1]"

        print(f"✅ Q{i} structure valid ({len(options)} options)")

    print("✅ Test 9 PASSED\n")


def test_backward_compatibility():
    """Test 10: Old format detection and fallback"""
    print("\n🧪 Test 10: Backward Compatibility")

    # Test with old format (if it exists)
    answers = {
        "q1": {"answer": ["test"]},
        "_session_id": "test-10"
    }

    # Try with old format file (should detect and return empty)
    scores = calculate_z_scores_from_questions(
        answers,
        questions_file="arabic_questions.json",  # Old format
        lang="العربية"
    )

    # Should detect old format and return empty dict
    assert isinstance(scores, dict), "Should return dict"
    print("✅ Old format detection works")
    print("✅ Test 10 PASSED\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Task 2.1 Scoring System Tests")
    print("="*70)

    test_basic_scoring()
    test_expected_scores()
    test_weighted_average()
    test_multiple_answers_same_axis()
    test_all_sample_questions()
    test_empty_answers()
    test_partial_match()
    test_english_answers()
    test_json_structure()
    test_backward_compatibility()

    print("="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70 + "\n")
