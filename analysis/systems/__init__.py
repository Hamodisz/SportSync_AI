# -*- coding: utf-8 -*-
"""
analysis/systems/__init__.py
Multi-System Personality Analysis

الأنظمة الـ 15 للتحليل النفسي:
1. Big Five (OCEAN)
2. MBTI (Myers-Briggs)
3. Enneagram
4. DISC
5. Hexaco
6. Holland Codes (RIASEC)
7. Schwartz Values
8. Temperament Theory
9. Attachment Styles
10. Cognitive Functions (Jung)
11. Social Styles
12. StrengthsFinder Themes
13. Motivational Drives
14. Emotional Intelligence (EQ)
15. Sports Psychology Profile

كل نظام يعطي perspective مختلف
النظام يجمعهم ويطلع بـ "إجماع"
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class SystemProfile:
    """ملف شخصي من نظام واحد"""
    system_name: str
    profile: Dict[str, Any]
    confidence: float
    key_traits: List[str]
    sport_recommendations: List[str]

class MultiSystemAnalyzer:
    """محلل متعدد الأنظمة"""
    
    def __init__(self):
        self.systems = [
            "big_five",
            "mbti", 
            "enneagram",
            "disc",
            "hexaco",
            "riasec",
            "schwartz",
            "temperament",
            "attachment",
            "jung",
            "social_styles",
            "strengths",
            "motivations",
            "eq",
            "sports_psych"
        ]
    
    def analyze_all(self, answers: Dict[str, Any], 
                   lang: str = "العربية") -> Dict[str, SystemProfile]:
        """تحليل بجميع الأنظمة"""
        results = {}
        
        # كل نظام يحلل
        from .big_five import analyze_big_five
        from .mbti import analyze_mbti
        from .enneagram import analyze_enneagram
        # ... المزيد
        
        results["big_five"] = analyze_big_five(answers, lang)
        results["mbti"] = analyze_mbti(answers, lang)
        results["enneagram"] = analyze_enneagram(answers, lang)
        
        return results
    
    def get_consensus(self, profiles: Dict[str, SystemProfile]) -> Dict[str, Any]:
        """الإجماع بين الأنظمة"""
        
        # جمع التوصيات من كل الأنظمة
        all_sports = []
        for profile in profiles.values():
            all_sports.extend(profile.sport_recommendations)
        
        # عد التكرارات (voting)
        from collections import Counter
        sport_votes = Counter(all_sports)
        
        # أكثر 5 رياضات اتفاقاً
        top_sports = sport_votes.most_common(5)
        
        return {
            "consensus_sports": [s for s, _ in top_sports],
            "confidence": sum(p.confidence for p in profiles.values()) / len(profiles),
            "agreements": len(set(all_sports)),
            "profiles": profiles
        }

# Export
__all__ = ["MultiSystemAnalyzer", "SystemProfile"]
