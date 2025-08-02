# agents/marketing/brand_guardian.py

"""
هذا الوكيل مسؤول عن حماية هوية مشروع Sport Sync ومنع أي محتوى أو رد يخالف
قيم المشروع أو يُشوّه الرسالة العاطفية الذكية.

يمكن استدعاؤه في أي مرحلة لمراجعة النصوص أو فحص المنشورات أو مراجعة الشعار.
"""

def is_on_brand(content: str, lang: str = "en") -> bool:
    """
    يتحقق ما إذا كان المحتوى يتماشى مع نبرة وقيم Sport Sync_AI

    - يرفض أي محتوى تجاري رخيص أو ردود جافة أو مزيفة
    - يجب أن يعبر عن هدف المشروع: الهوية الرياضية لكل شخص
    """
    lowered = content.lower()

    forbidden_phrases = [
        "buy now", "limited time", "cheap", "burn calories", "lose weight fast",
        "clickbait", "miracle", "get ripped", "6-pack", "sale ends"
    ]

    required_phrases = [
        "find your sport", "your movement identity", "feel connected", "self-awareness",
        "emotional recommendation", "smart system", "long-term joy"
    ]

    if any(phrase in lowered for phrase in forbidden_phrases):
        return False

    if not any(phrase in lowered for phrase in required_phrases):
        return False

    return True


def enforce_brand_guidelines(text: str, lang: str = "en") -> str:
    """
    يصحح النص إذا كان لا يتماشى مع العلامة التجارية، ويعيد نسخة معدلة.

    مثال على التصحيح:
    - ❌ "Burn calories fast with this insane workout!"
    - ✅ "Discover your sport identity and enjoy movement that fits your soul."
    """
    if is_on_brand(text, lang):
        return text

    return (
        "Let’s rethink this message to align with Sport Sync’s vision. "
        "We don’t just promote exercise — we help people discover their *true movement identity*. "
        "Please rewrite this to reflect long-term emotional connection, not instant results."
    )
