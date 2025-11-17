"""
إضافات جديدة لـ backend_gpt.py
Task 1.1: ربط Dynamic Sports AI
"""

def calculate_confidence(z_scores: Dict[str, float]) -> float:
    """
    حساب درجة الثقة من z_scores
    
    عوامل الثقة:
    - قوة الإشارات (مدى وضوح الميول)
    - التناقضات (إذا كان solo عالي وgroup عالي معاً)
    - الاكتمال (هل جميع المحاور لها قيم واضحة)
    
    Returns:
        float: 0.0 (ثقة منخفضة جداً) إلى 1.0 (ثقة عالية جداً)
    """
    confidence = 0.0
    
    # 1. قوة الإشارات (30%)
    signals_strength = 0.0
    for axis, score in z_scores.items():
        if axis == "sensory_sensitivity":
            # 0 to 1 scale
            signals_strength += abs(score)
        else:
            # -1 to +1 scale
            signals_strength += abs(score)
    signals_strength = signals_strength / len(z_scores) if z_scores else 0
    confidence += signals_strength * 0.3
    
    # 2. التناقضات (30%)
    contradictions = 0.0
    # مثال: solo عالي + group عالي = تناقض
    if "solo_group" in z_scores:
        if abs(z_scores["solo_group"]) < 0.3:  # قريب من الوسط
            contradictions += 0.3
    # يمكن إضافة المزيد من التناقضات
    confidence += (1.0 - contradictions) * 0.3
    
    # 3. الاكتمال (40%)
    completeness = len([s for s in z_scores.values() if abs(s) > 0.2]) / len(z_scores) if z_scores else 0
    confidence += completeness * 0.4
    
    return min(1.0, max(0.0, confidence))


def _convert_dynamic_to_cards(
    sports: List[Dict[str, Any]],
    lang: str
) -> List[Dict[str, Any]]:
    """
    تحويل output Dynamic AI إلى format البطاقات المعتاد
    
    Dynamic AI يرجع:
    {
        "sport_name": "اسم الرياضة",
        "category": "هجين",
        "match_score": 0.95,
        "why_perfect": "...",
        "inner_sensation": "...",
        "first_week": "..."
    }
    
    البطاقات تحتاج:
    {
        "sport_label": "...",
        "what_it_looks_like": [...],
        "why_you": [...],
        "real_world": [...],
        ...
    }
    """
    cards = []
    
    for sport in sports:
        card = {
            "sport_label": sport.get("sport_name", "رياضة مخصصة"),
            "what_it_looks_like": [sport.get("inner_sensation", "")],
            "why_you": _parse_bullets(sport.get("why_perfect", "")),
            "real_world": _parse_bullets(sport.get("first_week", "")),
            "notes": [f"Match Score: {sport.get('match_score', 0.0):.0%}"],
            "mode": "dynamic",  # علامة أنها من Dynamic AI
            "category": sport.get("category", "custom")
        }
        cards.append(card)
    
    return cards


def _parse_bullets(text: str) -> List[str]:
    """تحويل نص إلى قائمة نقاط"""
    if not text:
        return []
    # إذا كان النص يحتوي bullets بالفعل
    if "\n-" in text or "\n•" in text:
        return [line.strip("- •").strip() for line in text.split("\n") if line.strip()]
    # إذا كان جملة واحدة طويلة، قسّمها
    sentences = text.split(".")
    return [s.strip() + "." for s in sentences if s.strip()]
