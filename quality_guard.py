# core/quality_guard.py
# حارس الجودة: يكتشف السطحية ويشرح الأسباب، ويستخدمه backend لإجبار التعميق.

import re

# قائمة أولية لأسماء/كلمات رياضية شائعة بالعربي/الإنجليزي (وسّعها لاحقًا إذا احتجت)
SPORT_WORDS_PATTERN = r"(كرة|قدم|سلة|طائرة|تنس|سباحة|جري|ركض|قوة|مقاومة|أثقال|كمال|ملاكمة|بوكس|كيك بوكس|جوجيتسو|تايكواندو|يوغا|بيلاتس|دراج|دراجة|دراجة ثابتة|cycling|run|runner|jog|jogging|swim|yoga|pilates|boxing|mma|football|soccer|basketball|tennis|strength|resistance|weight|weights|calisthenics|bodyweight|row|rowing|ski|skating)"

# عبارات عامة ممنوعة (سطحية)
GENERIC_PHRASES = [
    "أي نشاط بدني مفيد", "اختر ما يناسبك", "جرّب أكثر من خيار", "ابدأ بأي شيء",
    "تحرك فقط", "لا يهم النوع", "نشاط عام", "رياضة عامة", "أنت تعرف ما يناسبك"
]

# إشارات حسّية/عاطفية نريد كثافة منها
SENSORY_TOKENS = [
    "تنفّس","إيقاع","توتّر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","موجة","هدير","امتداد","حرق لطيف","صفاء","تماسك"
]

def mentions_sport_name(text: str) -> bool:
    return re.search(SPORT_WORDS_PATTERN, text, flags=re.IGNORECASE) is not None

def too_generic(text: str, min_chars: int = 420) -> bool:
    t = text.strip()
    if len(t) < min_chars:
        return True
    return any(p in t for p in GENERIC_PHRASES)

def poor_sensory_density(text: str, min_hits: int = 4) -> bool:
    hits = sum(1 for w in SENSORY_TOKENS if w in text)
    return hits < min_hits

def fails_layer_z(text: str) -> bool:
    # لازم يتضمن الثلاث أسطر المفصلّة لكل تجربة
    need = ["الدافع الصامت", "الطقس الأسبوعي", "إشارات شعورية"]
    return any(k not in text for k in need)

def is_superficial(text: str):
    """
    يرجع (is_bad, reasons[list[str]])
    """
    reasons = []
    if mentions_sport_name(text):  reasons.append("ذكر اسم رياضة")
    if too_generic(text):          reasons.append("قصير/عام")
    if poor_sensory_density(text): reasons.append("كثافة حسّية ضعيفة")
    if fails_layer_z(text):        reasons.append("نواقص بنية Layer Z")
    return (len(reasons) > 0, reasons)

def strip_sport_words(text: str) -> str:
    return re.sub(SPORT_WORDS_PATTERN, "—", text, flags=re.IGNORECASE)
