# -*- coding: utf-8 -*-
"""
analysis/systems/big_five.py
Big Five (OCEAN) Analysis

الأبعاد الخمسة الكبرى:
1. Openness (الانفتاح)
2. Conscientiousness (الضمير/التنظيم)
3. Extraversion (الانبساط)
4. Agreeableness (الطيبة)
5. Neuroticism (العصابية)
"""

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class BigFiveProfile:
    openness: float  # 0-1
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    
    def to_dict(self):
        return {
            "O": self.openness,
            "C": self.conscientiousness,
            "E": self.extraversion,
            "A": self.agreeableness,
            "N": self.neuroticism
        }

def analyze_big_five(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    """
    تحليل Big Five من الإجابات
    
    الطريقة: نحلل النص ونستنتج الأبعاد
    بدون حاجة لأسئلة Big Five التقليدية
    """
    
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
    
    # تحليل ذكي (patterns)
    profile = _infer_big_five(combined_text, lang)
    
    # توصيات رياضية بناءً على Big Five
    sport_recs = _big_five_to_sports(profile)
    
    return {
        "system_name": "Big Five (OCEAN)",
        "profile": profile.to_dict(),
        "confidence": 0.75,
        "key_traits": _interpret_big_five(profile, lang),
        "sport_recommendations": sport_recs
    }

def _infer_big_five(text: str, lang: str) -> BigFiveProfile:
    """استنتاج Big Five من النص"""
    
    # Openness indicators
    openness_words = ["جديد", "تجربة", "إبداع", "فن", "فكر", "خيال"]
    openness = min(sum(1 for w in openness_words if w in text) / 3, 1.0)
    
    # Conscientiousness indicators  
    conscien_words = ["منظم", "خطة", "دقيق", "التزام", "نظام", "ترتيب"]
    conscien = min(sum(1 for w in conscien_words if w in text) / 3, 1.0)
    
    # Extraversion indicators
    extra_words = ["ناس", "أصدقاء", "جماعي", "فريق", "اجتماعي", "حماس"]
    extra = min(sum(1 for w in extra_words if w in text) / 3, 1.0)
    
    # Agreeableness indicators
    agree_words = ["مساعدة", "تعاون", "طيب", "لطيف", "صديق", "محب"]
    agree = min(sum(1 for w in agree_words if w in text) / 3, 1.0)
    
    # Neuroticism indicators (عكسي - الهدوء)
    calm_words = ["هدوء", "راحة", "استرخاء", "سلام", "طمأنينة"]
    stress_words = ["توتر", "قلق", "ضغط", "عصبي"]
    neuroticism = max(0, min(
        sum(1 for w in stress_words if w in text) / 2 - 
        sum(1 for w in calm_words if w in text) / 2,
        1.0
    ))
    
    return BigFiveProfile(
        openness=openness,
        conscientiousness=conscien,
        extraversion=extra,
        agreeableness=agree,
        neuroticism=neuroticism
    )

def _interpret_big_five(profile: BigFiveProfile, lang: str) -> List[str]:
    """تفسير الملف"""
    ar = (lang == "العربية")
    traits = []
    
    if profile.openness > 0.6:
        traits.append("منفتح على التجارب" if ar else "Open to experience")
    elif profile.openness < 0.4:
        traits.append("يفضل المألوف" if ar else "Prefers familiar")
    
    if profile.conscientiousness > 0.6:
        traits.append("منظم ومنضبط" if ar else "Organized & disciplined")
    elif profile.conscientiousness < 0.4:
        traits.append("مرن وعفوي" if ar else "Flexible & spontaneous")
    
    if profile.extraversion > 0.6:
        traits.append("اجتماعي ومنبسط" if ar else "Social & extraverted")
    elif profile.extraversion < 0.4:
        traits.append("هادئ ومنطوٍ" if ar else "Quiet & introverted")
    
    if profile.agreeableness > 0.6:
        traits.append("متعاون ولطيف" if ar else "Cooperative & kind")
    
    if profile.neuroticism < 0.3:
        traits.append("مستقر عاطفياً" if ar else "Emotionally stable")
    
    return traits

def _big_five_to_sports(profile: BigFiveProfile) -> List[str]:
    """ترجمة Big Five إلى رياضات"""
    sports = []
    
    # Openness high → رياضات إبداعية
    if profile.openness > 0.6:
        sports.extend(["dance", "parkour", "skateboarding"])
    
    # Conscientiousness high → رياضات منظمة
    if profile.conscientiousness > 0.6:
        sports.extend(["archery", "golf", "chess"])
    
    # Extraversion high → رياضات جماعية
    if profile.extraversion > 0.6:
        sports.extend(["football", "basketball", "volleyball"])
    elif profile.extraversion < 0.4:
        sports.extend(["swimming", "running", "yoga"])
    
    # Agreeableness high → رياضات تعاونية
    if profile.agreeableness > 0.6:
        sports.extend(["team_sports", "partner_yoga"])
    
    # Neuroticism low → رياضات هادئة
    if profile.neuroticism < 0.3:
        sports.extend(["meditation", "tai_chi", "yoga"])
    
    return sports[:5]  # أول 5
