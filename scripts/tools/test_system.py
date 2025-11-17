#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Triple Intelligence System
===============================
Run comprehensive tests on the AI orchestrator
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.ai_orchestrator import get_ai_system
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_system():
    """Run comprehensive system test"""
    
    print("="* 60)
    print("🧪 TESTING TRIPLE INTELLIGENCE SYSTEM")
    print("=" * 60)
    print()
    
    # Check environment
    print("1️⃣ Checking environment...")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ FAILED: OPENAI_API_KEY not found!")
        print("   Please set it in .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    print()
    
    # Initialize system
    print("2️⃣ Initializing AI system...")
    try:
        system = get_ai_system()
        print("✅ System initialized successfully")
        print(f"   Models: {system.models}")
    except Exception as e:
        print(f"❌ FAILED to initialize: {e}")
        return False
    print()
    
    # Test Layer 1: Fast Analysis
    print("3️⃣ Testing Layer 1: Fast Analysis...")
    test_input = "أبحث عن رياضة هادئة تساعدني على التركيز"
    
    try:
        fast_response = system.analyze_user_fast(test_input, "ar")
        
        if fast_response.success:
            print("✅ Layer 1 SUCCESS")
            print(f"   Model: {fast_response.model_used}")
            print(f"   Tokens: {fast_response.tokens_used}")
            print(f"   Response preview: {fast_response.data[:100]}...")
        else:
            print(f"❌ Layer 1 FAILED: {fast_response.error}")
            return False
    except Exception as e:
        print(f"❌ Layer 1 EXCEPTION: {e}")
        return False
    print()
    
    # Test Layer 2: Deep Reasoning
    print("4️⃣ Testing Layer 2: Deep Reasoning...")
    try:
        deep_response = system.analyze_deep_reasoning(
            fast_response.data,
            test_input,
            "ar"
        )
        
        if deep_response.success:
            print("✅ Layer 2 SUCCESS")
            print(f"   Model: {deep_response.model_used}")
            print(f"   Tokens: {deep_response.tokens_used}")
            print(f"   Response preview: {deep_response.data[:100]}...")
        else:
            print(f"❌ Layer 2 FAILED: {deep_response.error}")
            return False
    except Exception as e:
        print(f"❌ Layer 2 EXCEPTION: {e}")
        return False
    print()
    
    # Test Layer 3: Intelligence
    print("5️⃣ Testing Layer 3: Intelligence...")
    try:
        intel_response = system.generate_recommendations(
            fast_response.data,
            deep_response.data,
            "ar"
        )
        
        if intel_response.success:
            print("✅ Layer 3 SUCCESS")
            print(f"   Model: {intel_response.model_used}")
            print(f"   Tokens: {intel_response.tokens_used}")
            print(f"   Response preview: {intel_response.data[:100]}...")
        else:
            print(f"❌ Layer 3 FAILED: {intel_response.error}")
            return False
    except Exception as e:
        print(f"❌ Layer 3 EXCEPTION: {e}")
        return False
    print()
    
    # Test Full Pipeline
    print("6️⃣ Testing Full Pipeline...")
    try:
        result = system.run_full_pipeline(test_input, "ar")
        
        if result["success"]:
            print("✅ FULL PIPELINE SUCCESS!")
            print(f"   Total tokens: {result['total_tokens']}")
            print(f"   All layers completed successfully")
            return True
        else:
            print("❌ PIPELINE FAILED")
            print(f"   Errors: {result['errors']}")
            return False
    except Exception as e:
        print(f"❌ PIPELINE EXCEPTION: {e}")
        return False


if __name__ == "__main__":
    print()
    success = test_system()
    print()
    print("=" * 60)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ System is ready for production")
    else:
        print("❌ TESTS FAILED!")
        print("⚠️  Please fix the issues above")
    
    print("=" * 60)
    sys.exit(0 if success else 1)
