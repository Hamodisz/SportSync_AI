# -*- coding: utf-8 -*-
"""
analysis/systems/enneagram.py
Enneagram Analysis - التساعي

9 أنواع شخصية أساسية:
1. المصلح (The Reformer)
2. المساعد (The Helper)  
3. المنجز (The Achiever)
4. الفردي (The Individualist)
5. الباحث (The Investigator)
6. المخلص (The Loyalist)
7. المتحمس (The Enthusiast)
8. المتحدي (The Challenger)
9. صانع السلام (The Peacemaker)
"""

from typing import Dict, Any, List

ENNEAGRAM_SPORTS = {
    1: ["yoga", "pilates", "golf", "archery"],  # المصلح - الدقة
    2: ["team_sports", "volleyball", "dance", "group_fitness"],  # المساعد - جماعي
    3: ["competitive_sports", "running", "triathlon", "tennis"],  # المنجز - إنجاز
    4: ["dance", "artistic_gymnastics", "figure_skating", "yoga"],  # الفردي - تعبير
    5: ["chess", "strategy_games", "swimming", "cycling"],  # الباحث - فردي
    6: ["martial_arts", "team_sports", "hiking", "group_activities"],  # المخلص - أمان
    7: ["adventure_sports", "parkour", "skateboarding", "surfing"],  # المتحمس - تنوع
    8: ["boxing", "martial_arts", "weightlifting", "football"],  # المتحدي - قوة
    9: ["yoga", "tai_chi", "swimming", "walking"]  # صانع السلام - هدوء
}

def analyze_enneagram(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    """تحليل Enneagram من الإجابات"""
    
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
    enne_type = _infer_enneagram(combined_text, lang)
    
    # توصيات رياضية
    sport_recs = ENNEAGRAM_SPORTS.get(enne_type, [])
    
    return {
        "system_name": "Enneagram",
        "profile": {"type": enne_type, "name": _get_enne_name(enne_type, lang)},
        "confidence": 0.65,
        "key_traits": _enne_traits(enne_type, lang),
        "sport_recommendations": sport_recs
    }

def _infer_enneagram(text: str, lang: str) -> int:
    """استنتاج نوع Enneagram"""
    
    scores = [0] * 9
    
    # Type 1 - المصلح (الكمال، النظام)
    if any(w in text for w in ["مثالي", "كامل", "صحيح", "نظام", "قواعد"]):
        scores[0] += 1
    
    # Type 2 - المساعد (المساعدة، العطاء)
    if any(w in text for w in ["مساعدة", "عطاء", "خدمة", "ناس"]):
        scores[1] += 1
    
    # Type 3 - المنجز (النجاح، الإنجاز)
    if any(w in text for w in ["نجاح", "إنجاز", "هدف", "تحقيق", "فوز"]):
        scores[2] += 1
    
    # Type 4 - الفردي (التفرد، العمق)
    if any(w in text for w in ["فريد", "مختلف", "خاص", "عميق", "فن"]):
        scores[3] += 1
    
    # Type 5 - الباحث (المعرفة، الفهم)
    if any(w in text for w in ["معرفة", "فهم", "تعلم", "بحث", "تفكير"]):
        scores[4] += 1
    
    # Type 6 - المخلص (الأمان، الولاء)
    if any(w in text for w in ["أمان", "ثقة", "ولاء", "حذر", "تأكد"]):
        scores[5] += 1
    
    # Type 7 - المتحمس (المرح، التنوع)
    if any(w in text for w in ["متعة", "مرح", "جديد", "تنويع", "حماس"]):
        scores[6] += 1
    
    # Type 8 - المتحدي (القوة، السيطرة)
    if any(w in text for w in ["قوة", "سيطرة", "تحكم", "قيادة", "تحدي"]):
        scores[7] += 1
    
    # Type 9 - صانع السلام (الهدوء، السلام)
    if any(w in text for w in ["هدوء", "سلام", "راحة", "وئام", "تجنب صراع"]):
        scores[8] += 1
    
    # أعلى نقاط
    max_score = max(scores)
    if max_score == 0:
        return 9  # افتراضي
    return scores.index(max_score) + 1

def _get_enne_name(enne_type: int, lang: str) -> str:
    """اسم النوع"""
    ar = (lang == "العربية")
    
    names_ar = {
        1: "المصلح",
        2: "المساعد",
        3: "المنجز",
        4: "الفردي",
        5: "الباحث",
        6: "المخلص",
        7: "المتحمس",
        8: "المتحدي",
        9: "صانع السلام"
    }
    
    names_en = {
        1: "The Reformer",
        2: "The Helper",
        3: "The Achiever",
        4: "The Individualist",
        5: "The Investigator",
        6: "The Loyalist",
        7: "The Enthusiast",
        8: "The Challenger",
        9: "The Peacemaker"
    }
    
    return names_ar.get(enne_type, str(enne_type)) if ar else names_en.get(enne_type, str(enne_type))

def _enne_traits(enne_type: int, lang: str) -> List[str]:
    """سمات النوع"""
    ar = (lang == "العربية")
    
    traits_ar = {
        1: ["يسعى للكمال", "منظم", "مبدئي"],
        2: ["يحب المساعدة", "متعاطف", "اجتماعي"],
        3: ["موجه نحو الهدف", "طموح", "متكيف"],
        4: ["يقدر الأصالة", "عميق", "حساس"],
        5: ["فضولي", "مفكر", "مستقل"],
        6: ["مخلص", "مسؤول", "حذر"],
        7: ["متحمس", "متفائل", "يحب التجديد"],
        8: ["قوي", "حاسم", "واثق"],
        9: ["هادئ", "صانع سلام", "متقبل"]
    }
    
    return traits_ar.get(enne_type, []) if ar else [str(enne_type)]
