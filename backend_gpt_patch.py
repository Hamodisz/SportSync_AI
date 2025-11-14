

def _llm_cards_dual_model(
    answers: Dict[str, Any],
    identity: Dict[str, float],
    drivers: List[str],
    lang: str,
    traits: Optional[Dict[str, float]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    UPDATED: Now uses Complete Sport System with Layer Z + Facts + 8000 Sports
    """
    
    # Try new advanced system first
    try:
        from core.recommendation_wrapper import generate_advanced_recommendations
        
        print("[DUAL_MODEL] Trying COMPLETE SPORT SYSTEM (v2.2)...")
        
        cards = generate_advanced_recommendations(
            answers=answers,
            identity=identity,
            traits=traits or {},
            drivers=drivers,
            lang=lang
        )
        
        if cards and len(cards) >= 3:
            print(f"[DUAL_MODEL] ✅ SUCCESS! Generated {len(cards)} cards using v2.2")
            return cards
        else:
            print("[DUAL_MODEL] v2.2 returned insufficient cards, falling back...")
            
    except Exception as e:
        print(f"[DUAL_MODEL] v2.2 failed: {e}, falling back to old system...")
    
    # Original dual model fallback (old system)
    if not DUAL_MODEL_ENABLED:
        return None
    
    print("[DUAL_MODEL] Using old dual-model system (fallback)...")
    
    # Rest of original code...
    return None


