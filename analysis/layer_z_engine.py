# logic/layer_z_engine.py

def analyze_silent_drivers_combined(answers: dict, questions: list, lang: str = "العربية") -> list:
    """
    تحليل Layer Z لاستخراج المحركات الخفية من إجابات المستخدم،
    بناءً على الأسئلة المعلّمة بـ "layer_z": true داخل ملف الأسئلة.

    ✅ يدعم اللغة العربية والإنجليزية
    ✅ مرن وقابل للتوسع
    ✅ يحلل الخيارات المكتوبة أو الحرة

    Returns:
        قائمة بالمحركات الصامتة + بعض الجمل التي تفسّرها
    """
    drivers = []
    explanation_lines = []

    def translate(ar, en):
        return ar if lang == "العربية" else en

    # تعريف الكلمات المفتاحية المرتبطة بكل محرك
    keyword_map = [
        {
            "label": translate("الاندماج الإبداعي", "Creative Flow"),
            "keywords": ["برمجة", "كتابة", "رسم", "تصميم", "programming", "writing", "drawing", "design"]
        },
        {
            "label": translate("الانغماس الحسي", "Sensory Immersion"),
            "keywords": ["لعب", "جيم", "قتال", "vr", "gaming", "combat", "action"]
        },
        {
            "label": translate("الهروب الذهني", "Mental Escape"),
            "keywords": ["مشاهدة", "قراءة", "استماع", "watching", "reading", "listening"]
        },
        {
            "label": translate("القوة الذاتية", "Inner Power"),
            "keywords": ["أنجزت", "تحدي", "achieved", "challenge"]
        },
        {
            "label": translate("التمكن العقلي", "Mental Mastery"),
            "keywords": ["حليت", "فهمت", "solved", "understood"]
        },
        {
            "label": translate("النجاة والسرعة", "Survival Instinct"),
            "keywords": ["هربت", "نجوت", "escaped", "survived"]
        },
        {
            "label": translate("غريزة السيطرة", "Control Drive"),
            "keywords": ["سلاح", "مسدس", "سيف", "gun", "weapon", "sword"]
        },
        {
            "label": translate("فضول تقني", "Tech Curiosity"),
            "keywords": ["جهاز", "تقنية", "device", "tech"]
        },
        {
            "label": translate("فضول تحليلي", "Analytical Curiosity"),
            "keywords": ["مكبر", "عدسة", "عدسات", "magnifier", "lens"]
        },
        {
            "label": translate("نمط تعلّم تحليلي", "Analytical Learner"),
            "keywords": ["أفهم", "أعرف", "understand", "learn first"]
        },
        {
            "label": translate("نمط تعلّم حركي", "Kinetic Learner"),
            "keywords": ["أجرب", "أبدأ", "أحاول", "try", "explore", "jump in"]
        },
        {
            "label": translate("يكره التكرار", "Dislikes Repetition"),
            "keywords": ["ملل", "ممل", "boring", "boredom"]
        },
        {
            "label": translate("يبحث عن وضوح التقدّم", "Seeks Progress Clarity"),
            "keywords": ["مافي هدف", "ما أحس بنتيجة", "no goal", "no result"]
        },
        {
            "label": translate("يفضل اللعب الفردي", "Prefers Solo Activities"),
            "keywords": ["الناس", "زحمة", "crowd", "people"]
        },
        {
            "label": translate("يركز على الإنجاز الشخصي", "Private Accomplishment"),
            "keywords": ["أنجز", "أكمل", "achieve", "complete"]
        },
        {
            "label": translate("يستمتع بالعوالم الداخلية", "Inner World Enjoyment"),
            "keywords": ["أكتب", "أفكر", "تفكير", "write", "think", "reflect"]
        },
    ]

    for q in questions:
        if isinstance(q, dict) and not q.get("layer_z", False):
            continue

        q_key = q["key"]
        response_list = answers.get(q_key, [])
        response_text = " ".join(response_list).lower()

        for kw_group in keyword_map:
            if any(kw.lower() in response_text for kw in kw_group["keywords"]):
                if kw_group["label"] not in drivers:
                    drivers.append(kw_group["label"])
                    explanation_lines.append(
                        f"{q['question_ar'] if lang == 'العربية' else q['question_en']}: {response_text}"
                    )

    return explanation_lines + drivers
