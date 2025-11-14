# -*- coding: utf-8 -*-
"""
analysis/systems/mbti.py
MBTI (Myers-Briggs Type Indicator) Analysis

الأبعاد الأربعة:
1. E/I - Extraversion/Introversion
2. S/N - Sensing/Intuition
3. T/F - Thinking/Feeling
4. J/P - Judging/Perceiving

16 نوع شخصية محتمل
"""

from typing import Dict, Any, List

MBTI_TYPES = {
    "INTJ": ["chess", "strategy_games", "archery", "swimming"],
    "INTP": ["chess", "rock_climbing", "cycling", "puzzles"],
    "ENTJ": ["martial_arts", "competitive_sports", "football", "tennis"],
    "ENTP": ["parkour", "rock_climbing", "skateboarding", "basketball"],
    "INFJ": ["yoga", "meditation", "swimming", "tai_chi"],
    "INFP": ["dance", "yoga", "nature_walks", "swimming"],
    "ENFJ": ["team_sports", "volleyball", "basketball", "dance"],
    "ENFP": ["dance", "team_sports", "adventure_sports", "volleyball"],
    "ISTJ": ["running", "golf", "archery", "swimming"],
    "ISFJ": ["yoga", "swimming", "walking", "gardening_sport"],
    "ESTJ": ["football", "boxing", "weightlifting", "running"],
    "ESFJ": ["team_sports", "volleyball", "dance", "aerobics"],
    "ISTP": ["martial_arts", "rock_climbing", "cycling", "motorsports"],
    "ISFP": ["dance", "skateboarding", "surfing", "yoga"],
    "ESTP": ["extreme_sports", "boxing", "parkour", "football"],
    "ESFP": ["dance", "team_sports", "volleyball", "adventure_sports"]
}

def analyze_mbti(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    """تحليل MBTI من الإجابات"""
    
    # جمع النصوص
    texts = []
    for k, v in answers.items():
        if k == "_session_id":
            continue
        if isinstance(v, dict):
            answer = v.get("answer", "")
            if isinstance(answer, list):
                texts.extend([str(i) for i in answer])
            else:
                texts.append(str(answer))
        else:
            texts.append(str(v))
    
    combined_text = " ".join(texts).lower()
    
    # تحديد النوع
    mbti_type = _infer_mbti_type(combined_text, lang)
    
    # توصيات رياضية
    sport_recs = MBTI_TYPES.get(mbti_type, [])
    
    return {
        "system_name": "MBTI",
        "profile": {"type": mbti_type, "description": _describe_mbti(mbti_type, lang)},
        "confidence": 0.70,
        "key_traits": _mbti_traits(mbti_type, lang),
        "sport_recommendations": sport_recs
    }

def _infer_mbti_type(text: str, lang: str) -> str:
    """استنتاج نوع MBTI"""
    
    # E vs I
    extro_words = ["ناس", "أصدقاء", "جماعي", "فريق"]
    intro_words = ["لوحدي", "هادئ", "وحيد", "خاص"]
    ei = "E" if sum(1 for w in extro_words if w in text) > sum(1 for w in intro_words if w in text) else "I"
    
    # S vs N
    sensing_words = ["واقعي", "عملي", "ملموس", "تفاصيل"]
    intuitive_words = ["خيال", "مستقبل", "إمكانيات", "نظرية"]
    sn = "S" if sum(1 for w in sensing_words if w in text) > sum(1 for w in intuitive_words if w in text) else "N"
    
    # T vs F
    thinking_words = ["منطق", "تحليل", "عقل", "موضوعي"]
    feeling_words = ["شعور", "إحساس", "عاطفة", "قلب"]
    tf = "T" if sum(1 for w in thinking_words if w in text) > sum(1 for w in feeling_words if w in text) else "F"
    
    # J vs P
    judging_words = ["خطة", "منظم", "نظام", "جدول"]
    perceiving_words = ["مرونة", "عفوي", "تلقائي", "حرية"]
    jp = "J" if sum(1 for w in judging_words if w in text) > sum(1 for w in perceiving_words if w in text) else "P"
    
    return f"{ei}{sn}{tf}{jp}"

def _describe_mbti(mbti_type: str, lang: str) -> str:
    """وصف النوع"""
    ar = (lang == "العربية")
    
    descriptions_ar = {
        "INTJ": "المهندس - استراتيجي ومستقل",
        "INTP": "المفكر - محلل وفضولي",
        "ENTJ": "القائد - حاسم وقوي",
        "ENTP": "المناظر - مبتكر ومتحمس",
        "INFJ": "المستشار - حالم ومثالي",
        "INFP": "الوسيط - هادئ ومبدع",
        "ENFJ": "المعلم - ملهم ومتعاطف",
        "ENFP": "المدافع - متحمس وإبداعي",
        "ISTJ": "المفتش - منظم وموثوق",
        "ISFJ": "المدافع - ودود ومخلص",
        "ESTJ": "المشرف - عملي ومنظم",
        "ESFJ": "المقدم - اجتماعي ومساعد",
        "ISTP": "الحرفي - عملي ومغامر",
        "ISFP": "الفنان - حساس ومرن",
        "ESTP": "المغامر - نشيط وجريء",
        "ESFP": "المسلي - مرح واجتماعي"
    }
    
    return descriptions_ar.get(mbti_type, mbti_type) if ar else mbti_type

def _mbti_traits(mbti_type: str, lang: str) -> List[str]:
    """سمات النوع"""
    ar = (lang == "العربية")
    
    traits_ar = {
        "INTJ": ["استراتيجي", "مستقل", "يحب التحديات الذهنية"],
        "INTP": ["محلل", "فضولي", "يحب حل المشكلات"],
        "ENTJ": ["قيادي", "حاسم", "موجه نحو الهدف"],
        "ENTP": ["مبتكر", "متحمس", "يحب النقاش"],
        "INFJ": ["حالم", "مثالي", "عميق"],
        "INFP": ["مبدع", "هادئ", "قيمي"],
        "ENFJ": ["ملهم", "متعاطف", "اجتماعي"],
        "ENFP": ["متحمس", "إبداعي", "اجتماعي"],
        "ISTJ": ["منظم", "موثوق", "عملي"],
        "ISFJ": ["مخلص", "ودود", "مساعد"],
        "ESTJ": ["منظم", "عملي", "حاسم"],
        "ESFJ": ["اجتماعي", "مساعد", "منظم"],
        "ISTP": ["عملي", "مغامر", "مرن"],
        "ISFP": ["فني", "حساس", "مرن"],
        "ESTP": ["نشيط", "جريء", "عملي"],
        "ESFP": ["مرح", "اجتماعي", "عفوي"]
    }
    
    return traits_ar.get(mbti_type, []) if ar else [mbti_type]
