# analysis/trait_summary.py

def summarize_traits(traits: dict) -> dict:
    """
    تلخيص السمات النفسية في شكل مختصر قابل للاستخدام
    """
    return {
        "core_emotion": traits.get("emotional_drive", "الدافع العاطفي غير معروف"),
        "movement_type": traits.get("preferred_motion", "أسلوب الحركة المفضل غير معروف"),
        "mental_pattern": traits.get("thought_loop", "نمط التفكير غير محدد"),
        "deep_pull": traits.get("silent_pull", "لا يوجد محفز خفي واضح")
    }
