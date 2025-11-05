# -*- coding: utf-8 -*-
"""
Recommendation Wrapper - Integration Point
==========================================
نقطة التكامل بين backend_gpt و النظام الجديد
"""

from typing import Dict, List, Any, Optional
import json


def generate_advanced_recommendations(
    answers: Dict[str, Any],
    identity: Dict[str, float],
    traits: Dict[str, float],
    drivers: List[str],
    lang: str
) -> Optional[List[Dict[str, Any]]]:
    """
    توليد توصيات متقدمة باستخدام النظام الكامل
    
    Returns:
        List of recommendation cards compatible with SportSync format
    """
    
    # Try complete system first
    try:
        from core.complete_sport_system import generate_complete_sport_recommendations
        
        print("[WRAPPER] Using complete sport system...")
        
        inventions = generate_complete_sport_recommendations(
            user_answers=answers,
            user_traits=traits,
            user_identity=identity,
            language=lang,
            num_recommendations=3
        )
        
        if inventions and len(inventions) > 0:
            # Convert to SportSync card format
            cards = []
            for inv in inventions:
                card = _convert_to_card_format(inv, lang)
                if card:
                    cards.append(card)
            
            if len(cards) > 0:
                print(f"[WRAPPER] ✅ Generated {len(cards)} cards using complete system")
                return cards
                
    except Exception as e:
        print(f"[WRAPPER] Complete system failed: {e}")
    
    # Fallback to dual model
    try:
        from core.dual_model_client import (
            analyze_user_with_discovery,
            invent_sport_identities_with_reasoning
        )
        
        print("[WRAPPER] Fallback to dual model...")
        
        # Step 1: Analyze
        analysis = analyze_user_with_discovery(
            answers=answers,
            identity=identity,
            traits=traits,
            lang=lang
        )
        
        # Step 2: Invent
        inventions = invent_sport_identities_with_reasoning(
            quick_analysis=analysis,
            traits=traits,
            drivers=drivers,
            lang=lang,
            num_inventions=3
        )
        
        if inventions:
            cards = []
            for inv in inventions:
                card = _convert_to_card_format(inv, lang)
                if card:
                    cards.append(card)
            
            if len(cards) > 0:
                print(f"[WRAPPER] ✅ Generated {len(cards)} cards using dual model")
                return cards
                
    except Exception as e:
        print(f"[WRAPPER] Dual model failed: {e}")
    
    print("[WRAPPER] ❌ All systems failed, returning None")
    return None


def _convert_to_card_format(invention: Dict, lang: str) -> Optional[Dict[str, Any]]:
    """
    تحويل الاختراع إلى صيغة بطاقة SportSync
    
    SportSync card format:
    {
        "sport_label": "...",
        "what": "...",  # 2-3 sentences
        "why": ["...", "...", "..."],  # 2-3 points
        "real": ["...", "...", "..."],  # 2-3 points
        "notes": ["...", "...", "..."]  # 2-3 points
    }
    """
    
    try:
        card = {}
        
        # sport_label
        card['sport_label'] = (
            invention.get('enhanced_label') or 
            invention.get('sport_label') or 
            'رياضة مخصصة' if lang in ('ar', 'العربية') else 'Custom Sport'
        )
        
        # what - description
        what_text = (
            invention.get('ai_description') or 
            invention.get('what') or 
            invention.get('tagline') or 
            ''
        )
        
        if isinstance(what_text, str):
            card['what'] = what_text
        elif isinstance(what_text, dict):
            card['what'] = what_text.get('description', str(what_text))
        else:
            card['what'] = str(what_text) if what_text else ''
        
        # why - reasons
        why_list = (
            invention.get('ai_reasons') or
            invention.get('why_you') or
            invention.get('why') or
            invention.get('reasons', [])
        )
        
        if isinstance(why_list, list):
            card['why'] = why_list[:3]
        elif isinstance(why_list, str):
            card['why'] = [why_list]
        else:
            card['why'] = []
        
        # real - reality/benefits
        real_list = invention.get('benefits', [])
        if not real_list:
            # Generate from DNA
            dna = invention.get('dna', {})
            if dna:
                if lang in ('ar', 'العربية'):
                    real_list = [
                        f"البيئة: {dna.get('environment', 'متنوعة')}",
                        f"نمط الحركة: {dna.get('movement', 'مرن')}",
                        f"الدافع الأساسي: {dna.get('core_drive', 'شخصي')}"
                    ]
                else:
                    real_list = [
                        f"Environment: {dna.get('environment', 'Varied')}",
                        f"Movement: {dna.get('movement', 'Flexible')}",
                        f"Core Drive: {dna.get('core_drive', 'Personal')}"
                    ]
        
        card['real'] = real_list[:3] if isinstance(real_list, list) else [str(real_list)]
        
        # notes - practical steps
        notes_list = invention.get('where_to_start', [])
        if not notes_list and 'first_week' in invention:
            first_week = invention['first_week']
            if isinstance(first_week, dict):
                notes_list = list(first_week.values())[:3]
        
        if not notes_list:
            if lang in ('ar', 'العربية'):
                notes_list = [
                    "ابدأ بجلسة تجريبية 10 دقائق",
                    "ركز على الشعور وليس الأداء",
                    "عدّل التجربة حسب راحتك"
                ]
            else:
                notes_list = [
                    "Start with 10-minute trial session",
                    "Focus on feeling not performance",
                    "Adjust experience to your comfort"
                ]
        
        card['notes'] = notes_list[:3] if isinstance(notes_list, list) else [str(notes_list)]
        
        # Validate card has all required fields
        required = ['sport_label', 'what', 'why', 'real', 'notes']
        for field in required:
            if field not in card or not card[field]:
                print(f"[WRAPPER] Warning: Card missing field '{field}'")
                return None
        
        return card
        
    except Exception as e:
        print(f"[WRAPPER] Error converting to card format: {e}")
        return None


__all__ = ['generate_advanced_recommendations']
