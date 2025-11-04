# -*- coding: utf-8 -*-
"""
Dual-Model LLM Client for SportSync
====================================
نظام ذكاء مزدوج يستخدم موديلين متخصصين:
1. Discovery Model (o4-mini): للاكتشاف السريع والتحليل الأولي
2. Reasoning Model (gpt-5): للتفكير العميق والاستنتاجات المعقدة

Architecture:
- Discovery Model: Quick analysis, pattern recognition, initial insights
- Reasoning Model: Deep thinking, complex analysis, final recommendations
"""

from __future__ import annotations
import os
import json
from typing import Dict, List, Optional, Any
from core.llm_client import make_llm_client_singleton, chat_once, _bootstrap_env

# Bootstrap environment
_bootstrap_env()

# Global clients
DISCOVERY_CLIENT: Optional[Any] = None
REASONING_CLIENT: Optional[Any] = None
DISCOVERY_MODEL: str = ""
REASONING_MODEL: str = ""


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
        "o4-mini"
    )
    REASONING_MODEL = (
        os.getenv("CHAT_MODEL_REASONING") or 
        os.getenv("REASONING_MODEL") or 
        "gpt-5"
    )
    
    print(f"[DUAL_MODEL] Initialized:")
    print(f"  - Discovery: {DISCOVERY_MODEL} (quick analysis)")
    print(f"  - Reasoning: {REASONING_MODEL} (deep thinking)")


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
    """
    _init_dual_models()
    
    if DISCOVERY_CLIENT is None:
        print("[DUAL_MODEL] No discovery client available")
        return _fallback_quick_analysis(identity, traits)
    
    # Prepare quick analysis prompt
    if lang in ('العربية', 'ar'):
        system_prompt = """أنت محلل سريع متخصص في اكتشاف الأنماط.
مهمتك: تحليل سريع لإجابات المستخدم واستخراج:
1. initial_insights: الرؤى الأولية
2. patterns: الأنماط الظاهرة
3. quick_profile: ملف شخصي أولي

قدم تحليلاً سريعاً ومركزاً على الأنماط الواضحة.
"""
    else:
        system_prompt = """You are a fast pattern recognition analyst.
Your task: Quick analysis of user responses to extract:
1. initial_insights
2. patterns
3. quick_profile

Provide fast, focused analysis on clear patterns.
"""
    
    analysis_data = {
        'user_answers': answers,
        'identity_scores': identity,
        'trait_scores': traits,
        'language': lang
    }
    
    user_prompt = json.dumps(analysis_data, ensure_ascii=False, indent=2)
    
    try:
        # Use discovery model for quick analysis
        raw_response = chat_once(
            DISCOVERY_CLIENT,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Quick analysis:\n{user_prompt}"}
            ],
            model=DISCOVERY_MODEL,
            temperature=0.4,  # Balanced for quick insights
            max_tokens=1200
        )
        
        # Parse JSON response
        analysis = json.loads(raw_response)
        print(f"[DISCOVERY] Quick analysis completed: {len(analysis)} insights")
        return analysis
        
    except Exception as e:
        print(f"[DISCOVERY] Failed: {e}")
        return _fallback_quick_analysis(identity, traits)


def generate_deep_recommendations_with_reasoning(
    quick_analysis: Dict[str, Any],
    drivers: List[str],
    lang: str
) -> Optional[List[Dict[str, Any]]]:
    """
    استخدام Reasoning Model للتفكير العميق وتوليد توصيات متقدمة
    
    Args:
        quick_analysis: نتائج التحليل السريع من Discovery Model
        drivers: الدوافع الأساسية
        lang: اللغة
        
    Returns:
        List of 3 deeply-analyzed sport recommendation cards
    """
    _init_dual_models()
    
    if REASONING_CLIENT is None:
        print("[DUAL_MODEL] No reasoning client available")
        return None
    
    # Prepare deep reasoning prompt
    if lang in ('العربية', 'ar'):
        system_prompt = """أنت مفكر استراتيجي عميق متخصص في الرياضة والسلوك البشري.
مهمتك: بناءً على التحليل الأولي، فكر بعمق وأنشئ 3 توصيات رياضية متقدمة.

كل توصية يجب أن تحتوي على:
- sport_label: اسم مبتكر للتجربة الرياضية
- what: وصف عميق للتجربة (3-4 جمل)
- why: تحليل عميق لماذا تناسب المستخدم (3-4 نقاط)
- real: رؤية واقعية شاملة (3-4 نقاط)
- notes: استراتيجيات البدء (3-4 نقاط)
- deep_insight: رؤية نفسية عميقة (2-3 جمل)

استخدم تفكيراً عميقاً واستراتيجياً لتقديم توصيات تحويلية.
"""
    else:
        system_prompt = """You are a deep strategic thinker specialized in sports and human behavior.
Your task: Based on quick analysis, think deeply and create 3 advanced sport recommendations.

Each recommendation must include:
- sport_label: Innovative experience name
- what: Deep experience description (3-4 sentences)
- why: Deep analysis of fit (3-4 points)
- real: Comprehensive reality vision (3-4 points)
- notes: Strategic starting points (3-4 points)
- deep_insight: Deep psychological insight (2-3 sentences)

Use deep, strategic thinking to provide transformative recommendations.
"""
    
    reasoning_data = {
        'quick_analysis': quick_analysis,
        'user_drivers': drivers,
        'language': lang,
        'think_deeply_about': ['psychology', 'motivation', 'long_term_fit', 'transformative_potential']
    }
    
    user_prompt = json.dumps(reasoning_data, ensure_ascii=False, indent=2)
    
    try:
        # Use reasoning model for deep thinking
        raw_response = chat_once(
            REASONING_CLIENT,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Think deeply and generate:\n{user_prompt}"}
            ],
            model=REASONING_MODEL,
            temperature=0.6,  # Balanced for deep reasoning
            max_tokens=3000
        )
        
        # Parse JSON response
        recommendations = json.loads(raw_response)
        
        if isinstance(recommendations, dict) and 'cards' in recommendations:
            cards = recommendations['cards']
        elif isinstance(recommendations, list):
            cards = recommendations
        else:
            print("[REASONING] Unexpected response format")
            return None
        
        print(f"[REASONING] Generated {len(cards)} deep recommendations")
        return cards[:3]
        
    except Exception as e:
        print(f"[REASONING] Failed: {e}")
        return None


def _fallback_quick_analysis(identity: Dict[str, float], traits: Dict[str, float]) -> Dict[str, Any]:
    """تحليل احتياطي بسيط في حالة فشل Discovery Model"""
    return {
        'initial_insights': {
            'primary_trait': max(traits.items(), key=lambda x: x[1])[0] if traits else 'balanced',
            'confidence': max(traits.values()) if traits else 0.5
        },
        'patterns': ['moderate_activity', 'flexible_approach'],
        'quick_profile': {
            'style': 'adaptable',
            'intensity_preference': 'moderate'
        }
    }


__all__ = [
    'analyze_user_with_discovery',
    'generate_deep_recommendations_with_reasoning',
]
