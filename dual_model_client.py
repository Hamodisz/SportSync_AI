# -*- coding: utf-8 -*-
"""
Dual-Model LLM Client for SportSync - WITH SPORT INVENTION
===========================================================
نظام ذكاء مزدوج يخترع رياضات فريدة:
1. Discovery Model (o4-mini): للاكتشاف السريع والتحليل الأولي
2. Reasoning Model (gpt-5): للتفكير العميق والاستنتاجات المعقدة
3. Sport Identity Generator: لاختراع الرياضة المثالية

Architecture:
- Discovery: Quick psychological profiling
- Reasoning: Deep motivational analysis  
- Generator: INVENTS unique sport identity
"""

from __future__ import annotations
import os
import json
from typing import Dict, List, Optional, Any
from core.llm_client import make_llm_client_singleton, chat_once, _bootstrap_env
from core.sport_identity_generator import get_sport_identity_generator

# Bootstrap environment
_bootstrap_env()

# Global clients
DISCOVERY_CLIENT: Optional[Any] = None
REASONING_CLIENT: Optional[Any] = None
DISCOVERY_MODEL: str = ""
REASONING_MODEL: str = ""

# Sport Identity Generator
SPORT_GENERATOR = get_sport_identity_generator()


def _init_dual_models():
    """تهيئة الموديلات المزدوجة"""
    global DISCOVERY_CLIENT, REASONING_CLIENT, DISCOVERY_MODEL, REASONING_MODEL
    
    if DISCOVERY_CLIENT is None:
        DISCOVERY_CLIENT = make_llm_client_singleton()
        REASONING_CLIENT = DISCOVERY_CLIENT  # Same client, different models
    
    # Get models from environment - prioritize new naming
    DISCOVERY_MODEL = (
        os.getenv("CHAT_MODEL_DISCOVERY") or 
        os.getenv("INTELLIGENCE_MODEL") or 
        os.getenv("AI_INTELLIGENCE_MODEL") or
        "gpt-4o-mini"  # Default: OpenAI fast model
    )
    REASONING_MODEL = (
        os.getenv("CHAT_MODEL_REASONING") or 
        os.getenv("REASONING_MODEL") or 
        os.getenv("AI_REASONING_MODEL") or
        "gpt-4o"  # Default: OpenAI reasoning model
    )
    
    print(f"[DUAL_MODEL] Initialized:")
    print(f"  - Discovery: {DISCOVERY_MODEL} (quick analysis)")
    print(f"  - Reasoning: {REASONING_MODEL} (deep thinking)")
    print(f"  - Generator: ACTIVE (sport invention)")


def analyze_user_with_discovery(
    answers: Dict[str, Any],
    identity: Dict[str, float],
    traits: Dict[str, float],
    lang: str
) -> Dict[str, Any]:
    """
    استخدام Discovery Model للتحليل السريع الأولي
    
    Returns:
        Dict containing:
        - initial_insights: الرؤى الأولية السريعة
        - patterns: الأنماط المكتشفة
        - quick_profile: الملف الشخصي السريع
        - psychological_traits: السمات النفسية المستخرجة
    """
    _init_dual_models()
    
    if DISCOVERY_CLIENT is None:
        print("[DUAL_MODEL] No discovery client available")
        return _fallback_quick_analysis(identity, traits)
    
    # Prepare quick analysis prompt
    if lang in ('العربية', 'ar'):
        system_prompt = """أنت محلل نفسي متخصص في اكتشاف الهوية الرياضية الفريدة.
مهمتك: تحليل سريع عميق لإجابات المستخدم واستخراج:
1. initial_insights: رؤى أولية عن شخصيته الرياضية
2. patterns: أنماط سلوكية ونفسية خفية
3. quick_profile: ملف شخصي مختصر
4. hidden_drives: دوافع مخفية (Layer Z)
5. sport_dna_hints: تلميحات لتركيب DNA الرياضة المثالية

تذكر: الهدف ليس توصية رياضة تقليدية، بل فهم عميق لاختراع رياضة فريدة له.
أعط إجابتك بصيغة JSON.
"""
    else:
        system_prompt = """You are a psychological analyst specialized in discovering unique athletic identities.
Your task: Quick deep analysis of user responses to extract:
1. initial_insights: Initial insights about their athletic identity
2. patterns: Hidden behavioral and psychological patterns
3. quick_profile: Concise personality profile
4. hidden_drives: Hidden motivations (Layer Z)
5. sport_dna_hints: Hints for synthesizing perfect sport DNA

Remember: The goal isn't recommending traditional sports, but deep understanding to INVENT a unique sport.
Respond in JSON format.
"""
    
    analysis_data = {
        'user_answers': answers,
        'identity_scores': identity,
        'trait_scores': traits,
        'language': lang,
        'analysis_depth': 'layer_z_enabled'
    }
    
    user_prompt = json.dumps(analysis_data, ensure_ascii=False, indent=2)
    
    try:
        # Use discovery model for quick analysis
        raw_response = chat_once(
            DISCOVERY_CLIENT,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze deeply:\n{user_prompt}"}
            ],
            model=DISCOVERY_MODEL,
            temperature=0.4,  # Balanced for quick insights
            max_tokens=1500
        )
        
        # Parse JSON response
        try:
            analysis = json.loads(raw_response)
        except:
            # Fallback if not valid JSON
            analysis = {
                "initial_insights": raw_response[:200],
                "patterns": ["quick_analysis_completed"],
                "quick_profile": "analyzed",
                "psychological_traits": traits
            }
        
        print(f"[DISCOVERY] Quick analysis completed: {len(analysis)} insights")
        return analysis
        
    except Exception as e:
        print(f"[DISCOVERY] Failed: {e}")
        return _fallback_quick_analysis(identity, traits)


def invent_sport_identities_with_reasoning(
    quick_analysis: Dict[str, Any],
    traits: Dict[str, float],
    drivers: List[str],
    lang: str,
    num_inventions: int = 3
) -> Optional[List[Dict[str, Any]]]:
    """
    استخدام Reasoning Model + Sport Generator لاختراع رياضات فريدة
    
    This is where the MAGIC happens - we INVENT sports, not recommend them
    
    Args:
        quick_analysis: نتائج التحليل السريع من Discovery Model
        traits: السمات النفسية
        drivers: الدوافع الأساسية
        lang: اللغة
        num_inventions: عدد الرياضات المخترعة (default: 3)
        
    Returns:
        List of INVENTED sport identities (not recommendations!)
    """
    _init_dual_models()
    
    if REASONING_CLIENT is None:
        print("[DUAL_MODEL] No reasoning client available - using generator only")
        return _generate_inventions_directly(traits, drivers, lang, num_inventions)
    
    # Prepare deep reasoning prompt for INVENTION
    if lang in ('العربية', 'ar'):
        system_prompt = """أنت مخترع رياضات متخصص في ابتكار تجارب رياضية فريدة.

مهمتك الأساسية: اختراع رياضات جديدة تماماً، لم توجد من قبل.

⚠️ ممنوع منعاً باتاً:
- كرة القدم، كرة السلة، كرة الطائرة
- السباحة، الجري، ركوب الدراجات (بشكل تقليدي)
- اليوجا، البيلاتس (بشكل عادي)
- أي رياضة تقليدية معروفة

✅ بدلاً من ذلك، اخترع رياضات مثل:
- "رحلة الدراجة الانعزالية" (Bikepacking Solitude Mode)
- "الرقص التعبيري الافتراضي" (Flow Dance VR Therapy)  
- "مقاتل الإيقاع التكتيكي" (Combat Rhythm Arena)
- "التأمل الحركي في الطبيعة" (Moving Meditation Wilderness)

كل رياضة يجب أن تحتوي على:
- sport_label: اسم إبداعي فريد
- tagline: شعار ملهم
- dna: تركيبة DNA الرياضة (البيئة، الحركة، الدافع)
- what: وصف عميق للتجربة (3-4 جمل)
- why_you: لماذا اخترعنا هذا لك بالذات (3-4 نقاط شخصية)
- first_week: خطة الأسبوع الأول العملية
- reality_mode: واقع حقيقي/افتراضي/مختلط + السبب
- match_score: 85-98% (لأن الرياضة مخترعة له)
- invented_for: "أنت فقط"

الإبداع والتخصيص هما الأساس!
أعط إجابتك بصيغة JSON: {"inventions": [...]}'
"""
    else:
        system_prompt = """You are a sports inventor specialized in creating unique athletic experiences.

Your PRIMARY mission: INVENT completely new sports that never existed before.

⚠️ STRICTLY FORBIDDEN:
- Football, Basketball, Volleyball  
- Swimming, Running, Cycling (traditional forms)
- Yoga, Pilates (standard forms)
- Any traditional/known sport

✅ Instead, INVENT sports like:
- "Bikepacking Solitude Mode"
- "Flow Dance VR Therapy"
- "Combat Rhythm Arena"
- "Moving Meditation Wilderness"

Each sport must include:
- sport_label: Creative unique name
- tagline: Inspiring motto
- dna: Sport DNA composition (environment, movement, drive)
- what: Deep experience description (3-4 sentences)
- why_you: Why we invented THIS for YOU specifically (3-4 personal points)
- first_week: Practical week-one plan
- reality_mode: Real/VR/Mixed + reason
- match_score: 85-98% (because invented for them)
- invented_for: "Only YOU"

Creativity and personalization are EVERYTHING!
Respond in JSON format: {"inventions": [...]}
"""
    
    invention_data = {
        'quick_analysis': quick_analysis,
        'psychological_traits': traits,
        'user_drivers': drivers,
        'language': lang,
        'mission': 'INVENT_UNIQUE_SPORTS',
        'forbidden': ['football', 'swimming', 'running', 'yoga', 'basketball']
    }
    
    user_prompt = json.dumps(invention_data, ensure_ascii=False, indent=2)
    
    try:
        # Use reasoning model for deep invention
        raw_response = chat_once(
            REASONING_CLIENT,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Invent {num_inventions} unique sports:\n{user_prompt}"}
            ],
            model=REASONING_MODEL,
            temperature=0.8,  # Higher for creativity
            max_tokens=3500
        )
        
        # Parse JSON response
        try:
            result = json.loads(raw_response)
            inventions = result.get('inventions', [])
        except:
            print("[REASONING] Failed to parse JSON, using generator")
            return _generate_inventions_directly(traits, drivers, lang, num_inventions)
        
        if not inventions or len(inventions) == 0:
            print("[REASONING] No inventions generated, using direct generator")
            return _generate_inventions_directly(traits, drivers, lang, num_inventions)
        
        print(f"[REASONING] Invented {len(inventions)} unique sports!")
        
        # Enhance with Sport Generator DNA
        for invention in inventions:
            if 'dna' not in invention or not invention['dna']:
                sport_dna = SPORT_GENERATOR._synthesize_sport_dna(traits, quick_analysis, lang)
                invention['dna'] = sport_dna
            
            if 'match_score' not in invention:
                invention['match_score'] = SPORT_GENERATOR._calculate_match_score(traits, invention.get('dna', {}))
        
        return inventions[:num_inventions]
        
    except Exception as e:
        print(f"[REASONING] Failed: {e}")
        return _generate_inventions_directly(traits, drivers, lang, num_inventions)


def _generate_inventions_directly(
    traits: Dict[str, float],
    drivers: List[str],
    lang: str,
    num: int = 3
) -> List[Dict[str, Any]]:
    """
    توليد الرياضات مباشرة باستخدام Sport Generator (fallback)
    """
    inventions = []
    
    for i in range(num):
        # Generate unique sport for this iteration
        layer_z = {
            'drivers': drivers,
            'iteration': i,
            'variation_seed': i * 17  # For variety
        }
        
        invention = SPORT_GENERATOR.generate_sport_identity(
            user_traits=traits,
            layer_z=layer_z,
            language=lang
        )
        
        inventions.append(invention)
    
    print(f"[GENERATOR] Directly invented {len(inventions)} unique sports")
    return inventions


def _fallback_quick_analysis(identity: Dict[str, float], traits: Dict[str, float]) -> Dict[str, Any]:
    """تحليل احتياطي بسيط في حالة فشل Discovery Model"""
    return {
        'initial_insights': {
            'primary_trait': max(traits.items(), key=lambda x: x[1])[0] if traits else 'balanced',
            'confidence': max(traits.values()) if traits else 0.5
        },
        'patterns': ['moderate_activity', 'flexible_approach', 'unique_identity_seeker'],
        'quick_profile': {
            'style': 'adaptable',
            'intensity_preference': 'moderate',
            'social_mode': 'flexible'
        },
        'psychological_traits': traits,
        'hidden_drives': list(identity.keys())[:3] if identity else ['exploration']
    }


__all__ = [
    'analyze_user_with_discovery',
    'invent_sport_identities_with_reasoning',
]
