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

def analyze_all_systems(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    """
    دالة شاملة تحلل بجميع الأنظمة الـ 15 وتطلع بالإجماع

    Args:
        answers: إجابات المستخدم
        lang: اللغة (العربية أو English)

    Returns:
        {
            "systems": {system_name: analysis_result, ...},
            "consensus": {
                "top_sports": [...],
                "confidence": 0.85,
                "agreements": 12
            },
            "summary": {...}
        }
    """
    try:
        # استيراد الأنظمة الثلاثة الرئيسية
        from .big_five import analyze_big_five
        from .mbti import analyze_mbti
        from .enneagram import analyze_enneagram

        # استيراد الأنظمة الإضافية من quick_systems
        from .quick_systems import (
            analyze_disc,
            analyze_riasec,
            analyze_temperament,
            analyze_eq,
            analyze_sports_psych
        )

        results = {}

        # تحليل الأنظمة الرئيسية
        try:
            results["big_five"] = analyze_big_five(answers, lang)
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ Big Five failed: {e}")

        try:
            results["mbti"] = analyze_mbti(answers, lang)
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ MBTI failed: {e}")

        try:
            results["enneagram"] = analyze_enneagram(answers, lang)
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ Enneagram failed: {e}")

        # جمع النصوص للأنظمة الإضافية
        texts = []
        for k, v in answers.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict):
                answer = v.get("answer", "")
                if isinstance(answer, list):
                    texts.extend([str(i) for i in answer])
                else:
                    texts.append(str(answer))
            else:
                texts.append(str(v))
        combined_text = " ".join(texts)

        # تحليل الأنظمة الإضافية
        try:
            disc = analyze_disc(combined_text)
            results["disc"] = {
                "system_name": "DISC",
                "profile": disc["profile"],
                "confidence": 0.65,
                "key_traits": [],
                "sport_recommendations": disc["sports"]
            }
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ DISC failed: {e}")

        try:
            riasec = analyze_riasec(combined_text)
            results["riasec"] = {
                "system_name": "Holland (RIASEC)",
                "profile": riasec["profile"],
                "confidence": 0.65,
                "key_traits": [],
                "sport_recommendations": riasec["sports"]
            }
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ RIASEC failed: {e}")

        try:
            temp = analyze_temperament(combined_text)
            results["temperament"] = {
                "system_name": "Temperament",
                "profile": temp["profile"],
                "confidence": 0.60,
                "key_traits": [],
                "sport_recommendations": temp["sports"]
            }
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ Temperament failed: {e}")

        try:
            eq = analyze_eq(combined_text)
            results["eq"] = {
                "system_name": "Emotional Intelligence",
                "profile": eq["profile"],
                "confidence": 0.60,
                "key_traits": [],
                "sport_recommendations": eq["sports"]
            }
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ EQ failed: {e}")

        try:
            psych = analyze_sports_psych(combined_text)
            results["sports_psych"] = {
                "system_name": "Sports Psychology",
                "profile": psych["profile"],
                "confidence": 0.70,
                "key_traits": [],
                "sport_recommendations": psych["sports"]
            }
        except Exception as e:
            print(f"[SYSTEMS] ⚠️ Sports Psych failed: {e}")

        # حساب الإجماع (Consensus)
        consensus = _calculate_consensus(results)

        # ملخص
        summary = {
            "total_systems": len(results),
            "avg_confidence": sum(s.get("confidence", 0) for s in results.values()) / max(len(results), 1),
            "top_system": max(results.items(), key=lambda x: x[1].get("confidence", 0))[0] if results else None
        }

        print(f"[SYSTEMS] ✅ Analyzed {len(results)} systems")
        print(f"[SYSTEMS]    Top {len(consensus['top_sports'])} sports by consensus")
        print(f"[SYSTEMS]    Avg confidence: {summary['avg_confidence']:.2f}")

        return {
            "systems": results,
            "consensus": consensus,
            "summary": summary
        }

    except Exception as e:
        print(f"[SYSTEMS] ❌ analyze_all_systems failed: {e}")
        return {
            "systems": {},
            "consensus": {"top_sports": [], "confidence": 0.0, "agreements": 0},
            "summary": {"total_systems": 0, "avg_confidence": 0.0, "top_system": None}
        }


def _calculate_consensus(systems: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """حساب الإجماع بين الأنظمة المختلفة"""
    from collections import Counter

    # جمع كل التوصيات الرياضية
    all_sports = []
    for system_result in systems.values():
        sports = system_result.get("sport_recommendations", [])
        all_sports.extend(sports)

    if not all_sports:
        return {
            "top_sports": [],
            "confidence": 0.0,
            "agreements": 0,
            "sport_votes": {}
        }

    # عد التكرارات (Voting)
    sport_votes = Counter(all_sports)

    # أعلى 5 رياضات اتفاقاً
    top_sports = [sport for sport, _ in sport_votes.most_common(5)]

    # حساب confidence بناءً على الاتفاق
    max_votes = sport_votes.most_common(1)[0][1] if sport_votes else 0
    total_systems = len(systems)
    confidence = max_votes / max(total_systems, 1)

    return {
        "top_sports": top_sports,
        "confidence": min(confidence, 1.0),
        "agreements": len(set(all_sports)),  # عدد الرياضات الفريدة
        "sport_votes": dict(sport_votes.most_common(10))  # أعلى 10
    }


# Export
__all__ = ["MultiSystemAnalyzer", "SystemProfile", "analyze_all_systems"]
