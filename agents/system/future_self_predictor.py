# agents/system/silent_conflict_detector.py

"""
وكيل ذكي لتحليل التناقضات الصامتة داخل إجابات وتحليل المستخدم.
يُستخدم للكشف عن الفجوات أو الانحرافات بين ما يقوله المستخدم وبين ما يشعر به فعليًا.

يساعد النظام على:
- طرح أسئلة متابعة مخصصة
- تجنب توصيات سطحية
- تعميق فهم الهوية الرياضية الحقيقية
"""

def detect_silent_conflicts(analysis: dict, answers: dict) -> list:
    conflicts = []

    # مثال: يحب العزلة لكن يفضل فرق جماعية
    if analysis.get("prefers_solo") and "فريق" in str(answers).lower():
        conflicts.append("Contradiction: enjoys solitude but gravitates toward team-based environments.")

    # مثال: يبحث عن السلام لكنه ينجذب لرياضات عدوانية
    if analysis.get("values_peace") and any(s in str(answers).lower() for s in ["ملاكمة", "قتال", "ركل"]):
        conflicts.append("Silent driver mismatch: peaceful identity vs aggressive sport preference.")

    # طبقة Z: إذا دوافعه ناعمة لكن يختار تمارين خشنة
    layer_z = analysis.get("Layer Z", {})
    if "الانسياب" in str(layer_z.values()) and "جري سريع" in str(answers.values()):
        conflicts.append("Flow mismatch: prefers graceful flow but chooses rigid intensity.")

    return conflicts
