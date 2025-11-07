# -*- coding: utf-8 -*-
"""
EMERGENCY FIX - SportSync AI
============================
إصلاح شامل للمشاكل الحرجة:
1. تفعيل LLM (بدلاً من KB Ranker)
2. Streaming حقيقي للـ Chat
3. توصيات شخصية مختصرة
"""

import os
import sys

# ========================================
# المشاكل المكتشفة
# ========================================

PROBLEMS = {
    "1": {
        "issue": "❌ LLM معطل - النظام يستخدم KB Ranker (بطاقات جاهزة)",
        "location": "core/backend_gpt.py:1804",
        "cause": "Models غير موجودة: o4-mini, gpt-5",
        "fix": "استبدال بـ: gpt-4o-mini, gpt-4o"
    },
    "2": {
        "issue": "❌ Chat يعرض دفعة واحدة (بدون streaming)",
        "location": "quiz_service/app.py:492",
        "cause": "Buffering كل الـ chunks ثم عرضها معاً",
        "fix": "عرض كل chunk فور وصوله"
    },
    "3": {
        "issue": "❌ التوصيات طويلة جداً (800+ كلمة)",
        "location": "core/complete_sport_system.py:148",
        "cause": "System prompts طويلة وغير محددة",
        "fix": "تقصير max_tokens + system prompts مختصرة"
    }
}

# ========================================
# الإصلاحات
# ========================================

def fix_1_enable_llm():
    """إصلاح 1: تفعيل LLM"""
    env_path = "/Users/mohammadal-saati/SportSync_AI-1/.env"
    
    print("\n🔧 Fixing Problem 1: Enabling LLM...")
    
    # القراءة
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # الاستبدال
    content = content.replace(
        "CHAT_MODEL_DISCOVERY=o4-mini",
        "CHAT_MODEL_DISCOVERY=gpt-4o-mini"
    )
    content = content.replace(
        "CHAT_MODEL_REASONING=gpt-5",
        "CHAT_MODEL_REASONING=gpt-4o"
    )
    content = content.replace(
        "REASONING_MODEL=gpt-5",
        "REASONING_MODEL=gpt-4o"
    )
    content = content.replace(
        "INTELLIGENCE_MODEL=o4-mini",
        "INTELLIGENCE_MODEL=gpt-4o-mini"
    )
    
    # الكتابة
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ .env updated with correct models")
    print("   - Discovery: gpt-4o-mini")
    print("   - Reasoning: gpt-4o")


def fix_2_real_streaming():
    """إصلاح 2: Streaming حقيقي"""
    app_path = "/Users/mohammadal-saati/SportSync_AI-1/quiz_service/app.py"
    
    print("\n🔧 Fixing Problem 2: Real Streaming...")
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # البحث عن الكود القديم
    old_code = """                for chunk in start_dynamic_chat_stream(
                        answers=answers,
                        previous_recommendation=recs_for_chat,
                        ratings=ratings,
                        user_id="web_user",
                        lang=lang,
                        chat_history=st.session_state["chat_history"],
                        user_message=user_text
                    ):
                        buf.append(_safe_str(chunk))
                        if LIVE_TYPING:
                            ph.markdown("".join(_safe_str(x) for x in buf))
                    reply = "".join(_safe_str(x) for x in buf).strip()"""
    
    # الكود الجديد - streaming حقيقي
    new_code = """                for chunk in start_dynamic_chat_stream(
                        answers=answers,
                        previous_recommendation=recs_for_chat,
                        ratings=ratings,
                        user_id="web_user",
                        lang=lang,
                        chat_history=st.session_state["chat_history"],
                        user_message=user_text
                    ):
                        buf.append(_safe_str(chunk))
                        # عرض فوري لكل chunk - بدون انتظار
                        ph.markdown("".join(_safe_str(x) for x in buf))
                    reply = "".join(_safe_str(x) for x in buf).strip()"""
    
    content = content.replace(old_code, new_code)
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ app.py updated with real streaming")
    print("   - Removed conditional: if LIVE_TYPING")
    print("   - Now shows each chunk immediately")


def fix_3_compact_recommendations():
    """إصلاح 3: توصيات مختصرة"""
    system_path = "/Users/mohammadal-saati/SportSync_AI-1/core/complete_sport_system.py"
    
    print("\n🔧 Fixing Problem 3: Compact Recommendations...")
    
    with open(system_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # استبدال max_tokens
    content = content.replace(
        "max_tokens=2000",
        "max_tokens=600  # COMPACT: reduced from 2000"
    )
    
    with open(system_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ complete_sport_system.py updated")
    print("   - max_tokens: 2000 → 600")
    print("   - System prompts already updated (previous commit)")


def run_all_fixes():
    """تطبيق جميع الإصلاحات"""
    print("="*60)
    print("🚨 EMERGENCY FIX - SportSync AI")
    print("="*60)
    
    print("\n📋 Problems detected:")
    for key, problem in PROBLEMS.items():
        print(f"\n{key}. {problem['issue']}")
        print(f"   Location: {problem['location']}")
        print(f"   Cause: {problem['cause']}")
        print(f"   Fix: {problem['fix']}")
    
    print("\n" + "="*60)
    input("Press ENTER to apply ALL fixes... ")
    
    try:
        fix_1_enable_llm()
        fix_2_real_streaming()
        fix_3_compact_recommendations()
        
        print("\n" + "="*60)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("="*60)
        
        print("\n🚀 Next steps:")
        print("1. git add .")
        print("2. git commit -m 'fix: Enable LLM, real streaming, compact recommendations'")
        print("3. git push origin main")
        print("4. Render will auto-deploy")
        print("5. Monitor logs: https://dashboard.render.com/")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_all_fixes()
