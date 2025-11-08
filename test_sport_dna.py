#!/usr/bin/env python3
"""
اختبار سريع للـ Sport DNA Generator
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.sport_generator import SportDNAGenerator


def test_sport_generator():
    """
    اختبار بسيط للتأكد إن النظام يشتغل
    """
    print("=" * 60)
    print("🧬 اختبار Sport DNA Generator")
    print("=" * 60)
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return False
    
    # Create generator
    generator = SportDNAGenerator(api_key=api_key)
    print("✅ Generator initialized")
    
    # Test profile 1: Technical + Solo + Calm
    print("\n" + "=" * 60)
    print("Test 1: Technical + Solo + Calm")
    print("=" * 60)
    
    profile1 = {
        'technical_intuitive': 0.9,
        'solo_group': 0.85,
        'calm_adrenaline': 0.8,
        'sensory_sensitivity': 0.75
    }
    
    try:
        sport1 = generator.generate_unique_sport(profile1)
        
        print(f"\n✅ رياضة مولدة:")
        print(f"   الاسم: {sport1.get('name_ar', 'N/A')}")
        print(f"   Tagline: {sport1.get('tagline_ar', 'N/A')}")
        print(f"   الوصف: {sport1.get('description_ar', 'N/A')[:100]}...")
        print(f"   DNA Hash: {sport1.get('dna_hash', 'N/A')}")
        
        # Check uniqueness
        is_unique = generator.validate_uniqueness(sport1)
        if is_unique:
            print("   ✅ الرياضة فريدة (passed validation)")
        else:
            print("   ⚠️ الرياضة فشلت في فحص الفرادة")
        
    except Exception as e:
        print(f"❌ خطأ في التوليد: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test profile 2: Intuitive + Group + Adrenaline  
    print("\n" + "=" * 60)
    print("Test 2: Intuitive + Group + Adrenaline")
    print("=" * 60)
    
    profile2 = {
        'technical_intuitive': -0.7,
        'solo_group': -0.6,
        'calm_adrenaline': -0.8,
        'sensory_sensitivity': 0.4
    }
    
    try:
        sport2 = generator.generate_unique_sport(profile2)
        
        print(f"\n✅ رياضة مولدة:")
        print(f"   الاسم: {sport2.get('name_ar', 'N/A')}")
        print(f"   Tagline: {sport2.get('tagline_ar', 'N/A')}")
        print(f"   DNA Hash: {sport2.get('dna_hash', 'N/A')}")
        
        # Verify it's different from sport1
        if sport1.get('dna_hash') != sport2.get('dna_hash'):
            print("   ✅ الرياضة مختلفة عن السابقة")
        else:
            print("   ⚠️ نفس الرياضة! (مشكلة في التنوع)")
        
    except Exception as e:
        print(f"❌ خطأ في التوليد: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ الاختبار نجح!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_sport_generator()
    sys.exit(0 if success else 1)
