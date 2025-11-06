# -*- coding: utf-8 -*-
"""
Complete Sport Invention Integration
=====================================
النظام الكامل المتكامل:
- Layer Z (النية الخفية)
- Facts Layer (حقائق علمية)
- 8000 Sports Database
- Dual-Model AI (Discovery + Reasoning)
- Advanced Sport Inventor
"""

from typing import Dict, List, Any, Optional
import json

# Import all components
try:
    from core.advanced_sport_inventor import get_advanced_inventor
    from core.dual_model_client import (
        analyze_user_with_discovery,
        _init_dual_models
    )
    from core.llm_client import chat_once, make_llm_client_singleton
    FULL_SYSTEM_AVAILABLE = True
except Exception as e:
    print(f"[INTEGRATION] Import error: {e}")
    FULL_SYSTEM_AVAILABLE = False


def generate_complete_sport_recommendations(
    user_answers: Dict[str, Any],
    user_traits: Dict[str, float],
    user_identity: Dict[str, float],
    language: str = 'ar',
    num_recommendations: int = 3
) -> List[Dict[str, Any]]:
    """
    توليد التوصيات الكاملة باستخدام كل مكونات النظام
    
    الخطوات:
    1. Discovery Model: تحليل سريع
    2. Layer Z: استخراج النية الخفية
    3. Facts Layer: تطبيق القواعد العلمية
    4. Advanced Inventor: اختراع/دمج رياضات
    5. Reasoning Model: صقل وتحسين
    6. Final Output: 3 رياضات مخترعة/مخصصة
    
    Args:
        user_answers: إجابات المستخدم على الأسئلة
        user_traits: السمات النفسية (141+ trait)
        user_identity: الهوية (warrior, explorer, etc.)
        language: ar or en
        num_recommendations: عدد التوصيات (default: 3)
    
    Returns:
        List of invented/personalized sports
    """
    
    if not FULL_SYSTEM_AVAILABLE:
        return _fallback_recommendations(language)
    
    print("[INTEGRATION] Starting complete invention process...")
    
    # Step 1: Discovery Analysis
    print("[INTEGRATION] Step 1/6: Discovery Model analysis...")
    discovery_analysis = analyze_user_with_discovery(
        answers=user_answers,
        identity=user_identity,
        traits=user_traits,
        lang=language
    )
    
    # Step 2: Advanced Inventor
    print("[INTEGRATION] Step 2/6: Advanced Sport Invention...")
    inventor = get_advanced_inventor()
    
    # Generate multiple inventions
    inventions = []
    for i in range(num_recommendations):
        try:
            invention = inventor.invent_sport(
                user_answers=user_answers,
                traits=user_traits,
                lang=language
            )
            
            if invention:
                # Add discovery insights
                invention['discovery_insights'] = discovery_analysis.get('initial_insights', {})
                invention['layer_z_drivers'] = discovery_analysis.get('hidden_drives', [])
                inventions.append(invention)
                
        except Exception as e:
            print(f"[INTEGRATION] Invention {i} failed: {e}")
    
    # Step 3: Reasoning Model Enhancement
    print("[INTEGRATION] Step 3/6: Reasoning Model enhancement...")
    if len(inventions) > 0:
        inventions = _enhance_with_reasoning(inventions, discovery_analysis, language)
    
    # Step 4: Add AI-generated descriptions
    print("[INTEGRATION] Step 4/6: AI descriptions...")
    inventions = _add_ai_descriptions(inventions, user_traits, language)
    
    # Step 5: Validate and score
    print("[INTEGRATION] Step 5/6: Validation...")
    inventions = _validate_and_score(inventions, user_traits)
    
    # Step 6: Sort and return top N
    print("[INTEGRATION] Step 6/6: Finalization...")
    inventions.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    final_inventions = inventions[:num_recommendations]
    
    print(f"[INTEGRATION] ✅ Generated {len(final_inventions)} complete sport inventions")
    
    return final_inventions


def _enhance_with_reasoning(
    inventions: List[Dict],
    discovery_analysis: Dict,
    language: str
) -> List[Dict]:
    """
    تحسين الاختراعات باستخدام Reasoning Model
    """
    try:
        _init_dual_models()
        client = make_llm_client_singleton()
        
        if not client:
            return inventions
        
        # Prepare reasoning prompt
        reasoning_data = {
            'inventions': [
                {
                    'label': inv.get('sport_label'),
                    'base': inv.get('base_sport'),
                    'components': inv.get('hybrid_components', [])
                }
                for inv in inventions
            ],
            'discovery_analysis': discovery_analysis,
            'language': language
        }
        
        if language == 'ar':
            system_prompt = """أنت مستشار رياضي نفسي عميق. مهمتك: تشخيص الهوية الرياضية المخفية للشخص.

**القاعدة الذهبية:**
- لا تصف الرياضة فقط - شخّص العلاقة بين الشخص والرياضة
- استخدم لغة "أنت" المباشرة - المس الدوافع العميقة

**البنية الدقيقة:**

🎯 الرياضة المثالية لك: [اسم بالإنجليزية]

💡 ما هي؟
• [3-4 جمل قصيرة تصف التجربة والإحساس - ليس التاريخ]

🎮 ليه تناسبك؟
• أنت [صفة نفسية عميقة] - [ربط بالرياضة]
• [جملة ثانية تشرح الدافع الخفي]
• [جملة ثالثة تصف المتعة الحقيقية عندهم]

🔍 شكلها الواقعي:
• تدخل [وصف البداية]
• تستخدم [وصف التجربة الحية]
• [النتيجة النفسية] - "لكن داخلك تعرف إنك تنمو"

👁️‍🗨️ ملاحظات مهمة:
• [جملة واحدة قوية تلامس الهوية]
• [نصيحة عملية للبدء]

**مثال حقيقي:**
"أنت تكره التكرار، ترفض السطحية، وتحب توصل لجوهر الشي الحقيقي"

**الطول:** 120-180 كلمة فقط
**التركيز:** الهوية والشعور، ليس الوصف التقني

JSON format required.
"""
        else:
            system_prompt = """You are a deep sports psychologist. Your mission: Diagnose the hidden athletic identity.

**Golden Rule:**
- Don't just describe the sport - diagnose the relationship between person and sport
- Use direct "you" language - touch deep motivations

**Exact Structure:**

🎯 Your Perfect Sport: [English name]

💡 What is it?
• [3-4 short sentences describing EXPERIENCE and FEELING - not history]

🎮 Why it suits you?
• You [deep psychological trait] - [connection to sport]
• [Second sentence explaining hidden driver]
• [Third sentence describing their true pleasure]

🔍 What it looks like:
• You enter [describe start]
• You use [describe live experience]
• [Psychological result] - "but inside you know you're growing"

👁️‍🗨️ Important notes:
• [One powerful identity-touching sentence]
• [Practical advice to start]

**Real Example:**
"You hate repetition, reject superficiality, and love reaching the true essence of things"

**Length:** 120-180 words only
**Focus:** Identity and feeling, not technical description

JSON format required.
"""
        
        import os
        reasoning_model = os.getenv("CHAT_MODEL_REASONING", "gpt-4o")
        
        # إضافة السياق الشخصي العميق
        user_context = _build_personal_context(discovery_analysis, language)
        
        enhanced_json = chat_once(
            client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context + "\n\n" + json.dumps(reasoning_data, ensure_ascii=False)}
            ],
            model=reasoning_model,
            temperature=0.7,
            max_tokens=600  # REDUCED from 2000 for compact responses
        )
        
        # Parse and merge enhancements
        try:
            enhanced_data = json.loads(enhanced_json)
            enhanced_sports = enhanced_data.get('sports', [])
            
            for i, sport in enumerate(enhanced_sports):
                if i < len(inventions):
                    inventions[i]['enhanced_label'] = sport.get('enhanced_name', inventions[i].get('sport_label'))
                    inventions[i]['ai_description'] = sport.get('description', '')
                    inventions[i]['ai_reasons'] = sport.get('reasons', [])
        except:
            pass
        
    except Exception as e:
        print(f"[REASONING] Enhancement failed: {e}")
    
    return inventions


def _add_ai_descriptions(
    inventions: List[Dict],
    traits: Dict[str, float],
    language: str
) -> List[Dict]:
    """
    إضافة أوصاف AI للرياضات
    """
    for invention in inventions:
        if 'ai_description' not in invention:
            # Generate basic description
            label = invention.get('sport_label', 'رياضة مخصصة')
            
            if language == 'ar':
                invention['ai_description'] = f"{label} - تجربة رياضية فريدة مصممة خصيصاً لك"
            else:
                invention['ai_description'] = f"{label} - A unique athletic experience designed specifically for you"
    
    return inventions


def _validate_and_score(
    inventions: List[Dict],
    traits: Dict[str, float]
) -> List[Dict]:
    """
    التحقق من صحة الاختراعات وتقييمها
    + التأكد من الإيجاز والوضوح
    """
    for invention in inventions:
        # Validate description length (max 60 words)
        desc = invention.get('ai_description', '')
        if desc:
            words = desc.split()
            if len(words) > 60:
                invention['ai_description'] = ' '.join(words[:60]) + '...'
        
        # Validate reasons (max 3 points, each max 12 words)
        reasons = invention.get('ai_reasons', [])
        if len(reasons) > 3:
            reasons = reasons[:3]
        reasons = [' '.join(r.split()[:12]) for r in reasons]
        invention['ai_reasons'] = reasons
        
        # Calculate match score
        match_score = 0.85  # Base score
        
        # Bonus for having all fields
        if all(k in invention for k in ['sport_label', 'ai_description', 'ai_reasons']):
            match_score += 0.10
        
        invention['match_score'] = min(match_score, 1.0)
    
    return inventions
    التحقق من صحة الاختراعات وحساب الدرجات
    """
    for invention in inventions:
        # Ensure match_score exists
        if 'match_score' not in invention:
            invention['match_score'] = 85  # Default for invented sports
        
        # Validate required fields
        required_fields = ['sport_label']
        for field in required_fields:
            if field not in invention:
                invention[field] = 'Unknown Sport'
        
        # Add confidence score
        layer_z_confidence = invention.get('layer_z_drivers', [])
        if len(layer_z_confidence) >= 3:
            invention['confidence'] = 0.9
        else:
            invention['confidence'] = 0.7
    
    return inventions


def _fallback_recommendations(language: str) -> List[Dict]:
    """
    توصيات احتياطية في حالة فشل النظام
    """
    if language == 'ar':
        return [
            {
                'sport_label': 'رياضة مخصصة - المرحلة 1',
                'tagline': 'تجربة فريدة قيد التطوير',
                'match_score': 75,
                'fallback': True
            }
        ]
    else:
        return [
            {
                'sport_label': 'Custom Sport - Phase 1',
                'tagline': 'Unique experience in development',
                'match_score': 75,
                'fallback': True
            }
        ]


def _build_personal_context(discovery_analysis: Dict, language: str) -> str:
    """
    بناء السياق الشخصي العميق للمستخدم
    """
    
    # استخراج الهوية الأقوى
    identity_scores = discovery_analysis.get('identity_scores', {})
    dominant_identity = max(identity_scores.items(), key=lambda x: x[1])[0] if identity_scores else 'explorer'
    identity_strength = max(identity_scores.values()) if identity_scores else 0.5
    
    # استخراج الدوافع الخفية
    hidden_drivers = discovery_analysis.get('hidden_drives', [])[:3]
    
    # استخراج السمات النفسية الأقوى
    traits = discovery_analysis.get('traits_summary', {})
    top_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
    
    if language == 'ar':
        context = f"""
**السياق الشخصي العميق:**

🧬 **الهوية الأقوى:** {dominant_identity} ({identity_strength:.0%})
- هذا الشخص يميل بقوة نحو الهوية: {dominant_identity}

🔥 **الدوافع الخفية (Layer Z):**
{chr(10).join([f'• {driver}' for driver in hidden_drivers])}

🧠 **السمات النفسية الأقوى:**
{chr(10).join([f'• {trait}: {score:.0%}' for trait, score in top_traits])}

**مهمتك:**
اخترع/اختر رياضة تلامس هذه الهوية والدوافع بعمق.
استخدم لغة "أنت" المباشرة.
اجعلهم يشعرون "هذا أنا تماماً!".
"""
    else:
        context = f"""
**Deep Personal Context:**

🧬 **Dominant Identity:** {dominant_identity} ({identity_strength:.0%})
- This person strongly leans toward identity: {dominant_identity}

🔥 **Hidden Drivers (Layer Z):**
{chr(10).join([f'• {driver}' for driver in hidden_drivers])}

🧠 **Strongest Psychological Traits:**
{chr(10).join([f'• {trait}: {score:.0%}' for trait, score in top_traits])}

**Your Mission:**
Invent/choose a sport touching this identity and drivers deeply.
Use direct "you" language.
Make them feel "This is exactly ME!".
"""
    
    return context


__all__ = ['generate_complete_sport_recommendations']
