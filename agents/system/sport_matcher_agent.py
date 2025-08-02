# agents/system/sport_matcher_agent.py

"""
يربط بين تحليل الشخصية وبين الرياضة المناسبة.
هذا هو الوكيل المسؤول عن التوصية الرياضية الفعلية (الأساسية، البديلة، الابتكارية).
"""

def match_sports_from_traits(traits: dict, lang: str = "en") -> list:
    sport_1 = "Parkour" if traits.get("adventurous") else "Swimming"
    sport_2 = "Archery" if traits.get("focused") else "Dance"
    sport_3 = "VR Sword Fencing"  # توصية ابتكارية

    if lang == "ar":
        return [
            f"الرياضة الأنسب لك: {sport_1}",
            f"بديل ممكن تحبه: {sport_2}",
            f"اقتراح ذكي مبتكر: {sport_3}"
        ]
    else:
        return [
            f"Your best match: {sport_1}",
            f"Alternative sport you might love: {sport_2}",
            f"Creative suggestion: {sport_3}"
        ]
