# core/brand_signature.py

def add_brand_signature(prompt: str) -> str:
    """
    تضيف توقيع البراند الرسمي في نهاية التوصية.

    Args:
        prompt (str): النص الأساسي للتوصية.

    Returns:
        str: النص بعد إضافة توقيع Sports Sync.
    """
    signature = "\n\n— تم توليد هذه التوصية بواسطة Sport Sync AI 🤖"
    return prompt + signature