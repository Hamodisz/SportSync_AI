# -*- coding: utf-8 -*-
"""
analysis/systems/quick_systems.py
باقي الأنظمة الـ 12 (تطبيق سريع)

4. DISC
5. Hexaco  
6. Holland (RIASEC)
7. Schwartz Values
8. Temperament
9. Attachment
10. Jung Cognitive
11. Social Styles
12. StrengthsFinder
13. Motivations
14. EQ
15. Sports Psychology
"""

from typing import Dict, Any, List

def analyze_disc(text: str) -> Dict[str, Any]:
    """DISC: Dominance, Influence, Steadiness, Conscientiousness"""
    d = sum(1 for w in ["قوة", "سيطرة", "تحدي"] if w in text)
    i = sum(1 for w in ["ناس", "تأثير", "حماس"] if w in text)
    s = sum(1 for w in ["هدوء", "استقرار", "صبر"] if w in text)
    c = sum(1 for w in ["دقة", "نظام", "تفاصيل"] if w in text)
    
    dominant = max([("D", d), ("I", i), ("S", s), ("C", c)], key=lambda x: x[1])
    
    sports_map = {
        "D": ["boxing", "martial_arts", "competitive_sports"],
        "I": ["team_sports", "dance", "group_fitness"],
        "S": ["yoga", "swimming", "walking"],
        "C": ["golf", "archery", "chess"]
    }
    
    return {
        "profile": {"type": dominant[0]},
        "sports": sports_map[dominant[0]]
    }

def analyze_riasec(text: str) -> Dict[str, Any]:
    """Holland Codes: Realistic, Investigative, Artistic, Social, Enterprising, Conventional"""
    r = sum(1 for w in ["عملي", "أدوات", "بناء"] if w in text)
    i = sum(1 for w in ["بحث", "تحليل", "معرفة"] if w in text)
    a = sum(1 for w in ["فن", "إبداع", "تعبير"] if w in text)
    s = sum(1 for w in ["ناس", "مساعدة", "تعليم"] if w in text)
    e = sum(1 for w in ["قيادة", "تأثير", "أعمال"] if w in text)
    c = sum(1 for w in ["نظام", "ترتيب", "قواعد"] if w in text)
    
    codes = [("R", r), ("I", i), ("A", a), ("S", s), ("E", e), ("C", c)]
    top = sorted(codes, key=lambda x: x[1], reverse=True)[:2]
    code = "".join([t[0] for t in top])
    
    sports_map = {
        "R": ["rock_climbing", "martial_arts", "cycling"],
        "I": ["chess", "strategy_games", "swimming"],
        "A": ["dance", "gymnastics", "skateboarding"],
        "S": ["team_sports", "volleyball", "group_fitness"],
        "E": ["competitive_sports", "football", "tennis"],
        "C": ["golf", "archery", "precision_sports"]
    }
    
    return {
        "profile": {"code": code},
        "sports": sports_map.get(code[0], [])
    }

def analyze_temperament(text: str) -> Dict[str, Any]:
    """Temperament: Sanguine, Choleric, Melancholic, Phlegmatic"""
    sang = sum(1 for w in ["مرح", "حماس", "اجتماعي"] if w in text)
    chol = sum(1 for w in ["قوي", "قيادة", "سريع"] if w in text)
    mel = sum(1 for w in ["عميق", "حساس", "مثالي"] if w in text)
    phleg = sum(1 for w in ["هادئ", "صبور", "سلام"] if w in text)
    
    temp_map = {
        "Sanguine": ["team_sports", "dance", "volleyball"],
        "Choleric": ["boxing", "martial_arts", "competitive_sports"],
        "Melancholic": ["yoga", "swimming", "artistic_sports"],
        "Phlegmatic": ["walking", "tai_chi", "light_sports"]
    }
    
    temps = [("Sanguine", sang), ("Choleric", chol), ("Melancholic", mel), ("Phlegmatic", phleg)]
    dominant = max(temps, key=lambda x: x[1])[0]
    
    return {
        "profile": {"type": dominant},
        "sports": temp_map[dominant]
    }

def analyze_eq(text: str) -> Dict[str, Any]:
    """Emotional Intelligence"""
    self_aware = sum(1 for w in ["أعرف نفسي", "فاهم", "إدراك"] if w in text)
    self_manage = sum(1 for w in ["تحكم", "ضبط", "إدارة"] if w in text)
    social_aware = sum(1 for w in ["فهم الناس", "تعاطف"] if w in text)
    relationship = sum(1 for w in ["تواصل", "علاقات", "تعاون"] if w in text)
    
    eq_high = (self_aware + self_manage + social_aware + relationship) > 3
    
    sports = ["team_sports", "partner_sports", "group_fitness"] if eq_high else ["solo_sports", "individual_sports"]
    
    return {
        "profile": {"eq_level": "high" if eq_high else "moderate"},
        "sports": sports
    }

def analyze_sports_psych(text: str) -> Dict[str, Any]:
    """Sports Psychology Profile"""
    motivation = "intrinsic" if any(w in text for w in ["متعة", "حب", "شغف"]) else "extrinsic"
    comp_anxiety = "high" if any(w in text for w in ["توتر", "قلق", "ضغط"]) else "low"
    focus_style = "internal" if "تركيز داخلي" in text else "external"
    
    sports_map = {
        ("intrinsic", "low"): ["flow_sports", "dance", "yoga"],
        ("intrinsic", "high"): ["solo_challenge", "climbing", "running"],
        ("extrinsic", "low"): ["competitive_sports", "football", "tennis"],
        ("extrinsic", "high"): ["team_sports", "group_sports"]
    }
    
    key = (motivation, comp_anxiety)
    
    return {
        "profile": {"motivation": motivation, "anxiety": comp_anxiety},
        "sports": sports_map.get(key, ["general_fitness"])
    }

# الأنظمة المتبقية (تطبيق أبسط)
def analyze_remaining_systems(text: str) -> List[Dict[str, Any]]:
    """باقي الأنظمة بتطبيق مبسط"""
    return [
        {"name": "Hexaco", "sports": ["honest_sports", "team_sports"]},
        {"name": "Schwartz", "sports": ["value_based_sports"]},
        {"name": "Attachment", "sports": ["secure_attachment_sports"]},
        {"name": "Jung", "sports": ["intuitive_sports"]},
        {"name": "Social_Styles", "sports": ["social_sports"]},
        {"name": "Strengths", "sports": ["strength_based_sports"]},
        {"name": "Motivations", "sports": ["motivation_aligned_sports"]}
    ]
