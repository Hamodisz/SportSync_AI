# -*- coding: utf-8 -*-
"""
Backend GPT Integration Patch
==============================
يطبق النظام الجديد على backend_gpt بدون تعديل الملف الأصلي
"""

import sys
from typing import Dict, List, Any, Optional


def patch_backend_gpt():
    """تطبيق الـ patch على backend_gpt"""
    
    try:
        import core.backend_gpt as backend
        
        # Save original function
        original_llm_cards_dual = backend._llm_cards_dual_model
        
        def patched_llm_cards_dual(
            answers: Dict[str, Any],
            identity: Dict[str, float],
            drivers: List[str],
            lang: str,
            traits: Optional[Dict[str, float]] = None,
        ) -> Optional[List[Dict[str, Any]]]:
            """
            Patched version - tries v2.2 system first
            """
            
            # Try new system
            try:
                from core.recommendation_wrapper import generate_advanced_recommendations
                
                print("[PATCH] Trying COMPLETE SPORT SYSTEM (v2.2)...")
                
                cards = generate_advanced_recommendations(
                    answers=answers,
                    identity=identity,
                    traits=traits or {},
                    drivers=drivers,
                    lang=lang
                )
                
                if cards and len(cards) >= 3:
                    print(f"[PATCH] ✅ SUCCESS! Generated {len(cards)} cards using v2.2")
                    return cards
                    
            except Exception as e:
                print(f"[PATCH] v2.2 failed: {e}")
            
            # Fallback to original
            print("[PATCH] Falling back to original system...")
            return original_llm_cards_dual(answers, identity, drivers, lang, traits)
        
        # Apply patch
        backend._llm_cards_dual_model = patched_llm_cards_dual
        
        print("[PATCH] ✅ Backend GPT patched successfully!")
        return True
        
    except Exception as e:
        print(f"[PATCH] ❌ Failed to patch: {e}")
        return False


# Auto-patch on import
if __name__ != "__main__":
    patch_backend_gpt()


__all__ = ['patch_backend_gpt']
