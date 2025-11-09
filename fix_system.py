#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SportSync AI - System Fix & Integration Script
==============================================
هذا السكريبت يصلح جميع المشاكل ويدمج النظام المحسن

التحسينات:
✅ دعم مزودي LLM متعددين مع fallback
✅ معالجة أخطاء محسنة
✅ توافق كامل مع رؤية SportSync AI
✅ دعم 141+ طبقة تحليل نفسي
"""

import os
import sys
import shutil
from pathlib import Path

def fix_sportsync_system():
    """إصلاح وتحديث نظام SportSync AI"""
    
    print("🚀 SportSync AI - System Fix Starting...")
    print("=" * 50)
    
    # 1. Backup current llm_client.py
    project_root = Path(__file__).parent
    original_llm = project_root / "core" / "llm_client.py"
    backup_llm = project_root / "core" / "llm_client.py.backup"
    
    if original_llm.exists() and not backup_llm.exists():
        shutil.copy(original_llm, backup_llm)
        print("✅ Backed up original llm_client.py")
    
    # 2. Replace with enhanced version
    enhanced_llm = project_root / "core" / "llm_client_enhanced.py"
    if enhanced_llm.exists():
        shutil.copy(enhanced_llm, original_llm)
        print("✅ Installed enhanced LLM client")
    
    # 3. Check environment variables
    print("\n🔍 Checking API Keys...")
    
    api_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "GROQ_API_KEY": "Groq (Free tier available!)",
        "ANTHROPIC_API_KEY": "Anthropic Claude",
        "GOOGLE_API_KEY": "Google Gemini",
        "OPENROUTER_API_KEY": "OpenRouter",
        "DEEPSEEK_API_KEY": "DeepSeek"
    }
    
    available = []
    missing = []
    
    for key, name in api_keys.items():
        value = os.getenv(key, "").strip()
        if value and value != "YOUR_VALID_OPENAI_KEY_HERE":
            available.append(name)
            print(f"  ✅ {name}: Configured")
        else:
            missing.append((key, name))
            print(f"  ❌ {name}: Missing")
    
    if not available:
        print("\n⚠️ WARNING: No LLM providers configured!")
        print("Please add at least one API key to .env file")
        print("\n📌 Recommended (FREE options):")
        print("   1. Groq: https://console.groq.com/keys")
        print("   2. Google Gemini: https://makersuite.google.com/app/apikey")
        print("\n📌 Premium options:")
        print("   1. OpenAI: https://platform.openai.com/api-keys")
        print("   2. Anthropic: https://console.anthropic.com/")
    
    # 4. Test the system
    print("\n🧪 Testing LLM System...")
    try:
        from core.llm_client_enhanced import test_llm_system
        success = test_llm_system()
        if success:
            print("\n✅ System test passed!")
        else:
            print("\n⚠️ System test failed - please check API keys")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
    
    print("\n" + "=" * 50)
    print("📝 Summary:")
    print(f"  • Available providers: {len(available)}")
    print(f"  • Missing providers: {len(missing)}")
    
    if available:
        print(f"  • Working with: {', '.join(available)}")
        print("\n✨ SportSync AI is ready!")
        print("🎯 Vision: إيجاد الرياضة المثالية لكل شخص")
        return True
    else:
        print("\n❌ Please configure at least one LLM provider")
        return False

if __name__ == "__main__":
    success = fix_sportsync_system()
    sys.exit(0 if success else 1)
