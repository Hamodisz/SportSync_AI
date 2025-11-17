#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE SYSTEM TEST
==========================
اختبار شامل للنظام قبل الـ Push
"""

import sys
import json
sys.path.insert(0, '.')

def test_imports():
    """Test 1: Check all imports"""
    print("\n" + "="*60)
    print("TEST 1: Imports")
    print("="*60)
    
    try:
        from core.llm_client import make_llm_client_singleton
        print("✅ llm_client")
    except Exception as e:
        print(f"❌ llm_client: {e}")
        return False
    
    try:
        from core.advanced_sport_inventor import get_advanced_inventor
        print("✅ advanced_sport_inventor")
    except Exception as e:
        print(f"❌ advanced_sport_inventor: {e}")
        return False
    
    try:
        from core.dual_model_client import _init_dual_models
        print("✅ dual_model_client")
    except Exception as e:
        print(f"❌ dual_model_client: {e}")
        return False
    
    try:
        from core.complete_sport_system import generate_complete_sport_recommendations
        print("✅ complete_sport_system")
    except Exception as e:
        print(f"❌ complete_sport_system: {e}")
        return False
    
    return True


def test_generation():
    """Test 2: Generate recommendations"""
    print("\n" + "="*60)
    print("TEST 2: Generation")
    print("="*60)
    
    try:
        from core.complete_sport_system import generate_complete_sport_recommendations
        
        user_data = {
            'answers': {'q1': 'أكره الروتين'},
            'traits': {'novelty_preference': 0.9, 'challenge_seeking': 0.85},
            'identity': {'warrior': 0.7, 'strategist': 0.8}
        }
        
        result = generate_complete_sport_recommendations(
            user_answers=user_data['answers'],
            user_traits=user_data['traits'],
            user_identity=user_data['identity'],
            language='ar',
            num_recommendations=1
        )
        
        if not result or len(result) == 0:
            print("❌ No recommendations generated")
            return False
        
        rec = result[0]
        
        # Check fallback
        if rec.get('fallback', False):
            print("⚠️  Fallback recommendation (system not working)")
            return False
        
        print(f"✅ Generated: {rec.get('sport_name', 'N/A')}")
        print(f"   Score: {rec.get('match_score', 0)}")
        print(f"   Word count: {rec.get('word_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_structure():
    """Test 3: Check recommendation structure"""
    print("\n" + "="*60)
    print("TEST 3: Structure")
    print("="*60)
    
    try:
        from core.complete_sport_system import generate_complete_sport_recommendations
        
        user_data = {
            'answers': {'q1': 'test'},
            'traits': {'novelty_preference': 0.8},
            'identity': {'explorer': 0.7}
        }
        
        result = generate_complete_sport_recommendations(
            user_answers=user_data['answers'],
            user_traits=user_data['traits'],
            user_identity=user_data['identity'],
            language='ar',
            num_recommendations=1
        )
        
        if not result:
            print("❌ No result")
            return False
        
        rec = result[0]
        
        # Check required fields
        required = ['sport_name', 'what_is_it', 'why_suits_you', 'how_it_looks', 'important_notes']
        missing = [f for f in required if f not in rec]
        
        if missing:
            print(f"❌ Missing fields: {missing}")
            return False
        
        print("✅ All required fields present")
        print(f"   Fields: {list(rec.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Generation", test_generation),
        ("Structure", test_structure)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(p for _, p in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Ready for GitHub push!")
    else:
        print("❌ TESTS FAILED - Fix issues before pushing")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
