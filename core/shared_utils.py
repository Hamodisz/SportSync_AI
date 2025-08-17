# core/shared_utils.py

# =========================================================
# قيود مشتركة لمنع السطحية ومنع ذكر أسماء الرياضات
# =========================================================

# قائمة كلمات/أسماء رياضية شائعة تُذكر فقط داخل البرومبت كعناصر "ممنوع استخدامها".
# (مجرد توجيه للموديل – الفلترة الحقيقية تتم في backend إن رغبت)
_BANNED_SPORT_TERMS_AR = [
    "كرة","قدم","سلة","طائرة","تنس","سباحة","سبح","ركض","جري","مقاومة",
    "أثقال","رفع أثقال","كمال أجسام","ملاكمة","بوكس","كيك بوكس","جوجيتسو",
    "تايكواندو","يوغا","بيلاتس","دراج","دراجة","دراجة ثابتة","تزلج","تجديف",
    "سكواش","بادمنتون","كروس فت","باركور","تايت بو","سكوبا","غوص","فروسية"
]
_BANNED_SPORT_TERMS_EN = [
    "football","soccer","basketball","volleyball","tennis","swimming","run",
    "running","jogging","strength","resistance","weights","weightlifting",
    "bodybuilding","boxing","kickboxing","mma","bjj","jiu jitsu","taekwondo",
    "yoga","pilates","cycling","bike","biking","row","rowing","ski","skating",
    "crossfit","parkour","scuba","equestrian","horse riding"
]

# عبارات عامة تدل على السطحية (نذكرها للموديل ليتجنّبها)
_GENERIC_AVOID = [
    "أي نشاط بدني مفيد","اختر ما يناسبك","ابدأ بأي شيء","جرّب أكثر من خيار",
    "لا يهم النوع","تحرك فقط","نشاط عام","رياضة عامة","أنت تعرف ما يناسبك"
]

# مفردات حسّية نريد كثافة منها (لتذكير الموديل داخل البرومبت)
_SENSORY_TOKENS_AR = [
    "تنفّس","إيقاع","توتّر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","موجة","امتداد","حرق لطيف","صفاء","تماسك"
]


# ------------------------------
# [1] دالة توصية أعمق - للديناميكي (بدون أسماء)
# ------------------------------
def build_main_prompt(analysis, answers, personality, previous_recommendation, ratings, lang="العربية"):
    """
    تُستخدم في المحادثة الديناميكية لإنتاج توصية أعمق.
    تعديلات مهمة:
      - ممنوع ذكر أسماء رياضات؛ استخدم وصفاً حسّياً للمشهد/الإيقاع/السطح/التنفس/نوع الجهد.
      - اربط السبب بـ Layer Z بوضوح (لماذا أنت؟).
      - اعطِ خطة أسبوع أول + مؤشرات تقدم (2–4 أسابيع).
      - إذا انزلق اسم رياضة، استبدله بشرطة طويلة "—" وقدّم وصفاً حسّياً مكانه.
    """
    banned_ar = "، ".join(_BANNED_SPORT_TERMS_AR)
    banned_en = ", ".join(_BANNED_SPORT_TERMS_EN)
    avoid = "، ".join(_GENERIC_AVOID)
    sensory = "، ".join(_SENSORY_TOKENS_AR)

    if lang == "العربية":
        prompt = f"""👤 تحليل شخصية المستخدم:
{analysis}
"""

        if isinstance(analysis, dict) and "silent_drivers" in analysis and analysis["silent_drivers"]:
            prompt += "🧭 المحركات الصامتة:\n"
            for s in analysis["silent_drivers"]:
                prompt += f"- {s}\n"
            prompt += "\n"

        prompt += f"""🧠 ملف المدرب الذكي:
الاسم: {personality.get("name")}
النبرة: {personality.get("tone")}
الأسلوب: {personality.get("style")}
الفلسفة: {personality.get("philosophy")}

📝 إجابات المستخدم:
"""
        for k, v in (answers or {}).items():
            prompt += f"- {k}: {v}\n"

        prev1 = previous_recommendation[0] if previous_recommendation and len(previous_recommendation) > 0 else "—"
        prev2 = previous_recommendation[1] if previous_recommendation and len(previous_recommendation) > 1 else "—"
        prev3 = previous_recommendation[2] if previous_recommendation and len(previous_recommendation) > 2 else "—"

        prompt += f"""

📊 تقييم المستخدم للتوصيات السابقة:
{ratings}

📌 التوصيات الثلاثة التي قُدمت سابقًا:
1. {prev1}
2. {prev2}
3. {prev3}

⚠ قواعد صارمة (لا تكسرها):
- ممنوع ذكر أسماء رياضات نهائيًا. قائمة محظورة للأمثلة: [{banned_ar}] / [{banned_en}]
- إن انزلق اسم، استبدله فورًا بـ "—" وقدّم وصفًا حسّيًا بديلاً.
- تجنّب العبارات السطحية مثل: {avoid}
- استخدم لغة حسّية غنيّة (تذكير بالمفردات: {sensory})
- اربط التوصية مباشرةً بـ Layer Z (لماذا أنت؟ ما الذي يذيب وعيك؟ ما الدافع الداخلي؟)
- اعطِ خطة للأسبوع الأول (٣ خطوات عملية واضحة).
- اعطِ مؤشرات تقدّم محسوسة خلال 2–4 أسابيع.

✅ SELF‑CHECK (قبل الإخراج):
- لا توجد أي أسماء رياضات أو أدوات شهيرة حرفيًا.
- طول التوصية ≥ 6 جمل مفيدة.
- مذكور: (المشهد، الإحساس الداخلي، لماذا أنت/Layer Z، الملاءمة العملية، أول أسبوع، مؤشرات التقدم).

🎯 المطلوب الآن:
بناءً على كل ما سبق، أعطني توصية أعمق وأصدق بصيغة مقطع واحد بهذا القالب (من غير أسماء رياضات):
• المشهد: ...
• الإحساس الداخلي: ...
• لماذا أنت (Layer Z): ...
• الملاءمة العملية: (الزمن/المكان/التكلفة/الأمان) ...
• أول أسبوع: ...
• مؤشرات التقدم: ...

- كن ذكيًا، واقعيًا، وعاطفيًا. لا تكرر مضمون التوصيات السابقة، ولا تلمّح لأسمائها.
"""
    else:
        # English version mirrors the same constraints
        banned = ", ".join(_BANNED_SPORT_TERMS_EN)
        avoid_en = ", ".join(_GENERIC_AVOID)
        prompt = f"""👤 User Personality Analysis:
{analysis}
"""

        if isinstance(analysis, dict) and "silent_drivers" in analysis and analysis["silent_drivers"]:
            prompt += "🧭 Silent Drivers:\n"
            for s in analysis["silent_drivers"]:
                prompt += f"- {s}\n"
            prompt += "\n"

        prompt += f"""🧠 Smart Coach Profile:
Name: {personality.get("name")}
Tone: {personality.get("tone")}
Style: {personality.get("style")}
Philosophy: {personality.get("philosophy")}

📝 User's Questionnaire Answers:
"""
        for k, v in (answers or {}).items():
            prompt += f"- {k}: {v}\n"

        prev1 = previous_recommendation[0] if previous_recommendation and len(previous_recommendation) > 0 else "—"
        prev2 = previous_recommendation[1] if previous_recommendation and len(previous_recommendation) > 1 else "—"
        prev3 = previous_recommendation[2] if previous_recommendation and len(previous_recommendation) > 2 else "—"

        prompt += f"""

📊 User's Ratings on Previous Recommendations:
{ratings}

📌 Previous Three Recommendations:
1. {prev1}
2. {prev2}
3. {prev3}

⚠ Hard Rules (do not break):
- Do NOT name any sports. Banned examples: [{banned}]
- If a sport name slips, replace it with "—" and provide a sensory substitute.
- Avoid generic phrases: {avoid_en}
- Use rich sensory language (setting/surface/rhythm/breathing/type of effort).
- Tie rationale to Layer Z (why you? flow trigger? inner driver).
- Provide a First Week plan (3 concrete steps).
- Provide progress markers within 2–4 weeks.

✅ SELF‑CHECK before output:
- Zero sport/tool brand names.
- Length ≥ 6 meaningful sentences.
- Includes: Scene, Inner Sensation, Why you (Layer Z), Practical Fit, First Week, Progress Markers.

🎯 Your task:
Return ONE deeper recommendation (no sport names) using this template:
• Scene: ...
• Inner Sensation: ...
• Why you (Layer Z): ...
• Practical Fit (time/place/cost/safety): ...
• First Week: ...
• Progress Markers: ...

Be smart, realistic, and emotionally resonant. Do not repeat or allude to prior suggestions.
"""
    return prompt


# ------------------------------
# [2] دالة 3 توصيات رئيسية - للbackend (بدون أسماء)
# ------------------------------
def generate_main_prompt(analysis, answers, personality, lang="العربية"):
    """
    تُستخدم لتوليد 3 توصيات رئيسية بوضع "هوية بلا أسماء".
    """
    banned_ar = "، ".join(_BANNED_SPORT_TERMS_AR)
    banned_en = ", ".join(_BANNED_SPORT_TERMS_EN)
    avoid = "، ".join(_GENERIC_AVOID)
    sensory = "، ".join(_SENSORY_TOKENS_AR)

    if lang == "العربية":
        prompt = f"""🧠 تحليل المستخدم:
{analysis}
"""
        if isinstance(analysis, dict) and "silent_drivers" in analysis and analysis["silent_drivers"]:
            prompt += "🧭 المحركات الصامتة:\n"
            for s in analysis["silent_drivers"]:
                prompt += f"- {s}\n"
            prompt += "\n"

        prompt += f"""👤 الملف النفسي للمدرب الذكي:
الاسم: {personality.get("name")}
النبرة: {personality.get("tone")}
الأسلوب: {personality.get("style")}
الفلسفة: {personality.get("philosophy")}

📝 إجابات المستخدم على الاستبيان:
"""
        for k, v in (answers or {}).items():
            prompt += f"- {k}: {v}\n"

        prompt += f"""

⚠ قواعد صارمة:
- ممنوع ذكر أسماء رياضات نهائيًا. أمثلة محظورة: [{banned_ar}] / [{banned_en}]
- إن انزلق اسم، استبدله بـ "—" مع وصف حسّي بديل.
- تجنّب العبارات السطحية مثل: {avoid}
- زِد الكثافة الحسّية (تذكير بالمفردات: {sensory})
- اربط كل توصية بـ Layer Z بوضوح.

✅ SELF‑CHECK قبل الإخراج:
- لا توجد أسماء رياضات أو أدوات شهيرة.
- لكل توصية ≥ 6 جمل مفيدة، وتحتوي العناصر الستة المطلوبة.

🎯 أعطني ثلاث «تجارب حركة» بالضبط:

1) الهوية الأساسية:
   • المشهد: ...
   • الإحساس الداخلي: ...
   • لماذا أنت (Layer Z): ...
   • الملاءمة العملية: ...
   • أول أسبوع: ...
   • مؤشرات التقدم: ...

2) البديل الواقعي:
   • المشهد: ...
   • الإحساس الداخلي: ...
   • لماذا أنت (Layer Z): ...
   • الملاءمة العملية: ...
   • أول أسبوع: ...
   • مؤشرات التقدم: ...

3) الابتكارية/المزيج:
   • المشهد: ...
   • الإحساس الداخلي: ...
   • لماذا أنت (Layer Z): ...
   • الملاءمة العملية: ...
   • أول أسبوع: ...
   • مؤشرات التقدم: ...
"""
    else:
        banned = ", ".join(_BANNED_SPORT_TERMS_EN)
        avoid_en = ", ".join(_GENERIC_AVOID)

        prompt = f"""🧠 User Analysis:
{analysis}
"""
        if isinstance(analysis, dict) and "silent_drivers" in analysis and analysis["silent_drivers"]:
            prompt += "🧭 Silent Drivers:\n"
            for s in analysis["silent_drivers"]:
                prompt += f"- {s}\n"
            prompt += "\n"

        prompt += f"""👤 Smart Coach Profile:
Name: {personality.get("name")}
Tone: {personality.get("tone")}
Style: {personality.get("style")}
Philosophy: {personality.get("philosophy")}

📝 User Questionnaire Answers:
"""
        for k, v in (answers or {}).items():
            prompt += f"- {k}: {v}\n"

        prompt += f"""

⚠ Hard Rules:
- Absolutely NO sport names. Banned examples: [{banned}]
- If any slips, replace with "—" and describe the experience instead.
- Avoid generic phrases: {avoid_en}
- Increase sensory density (setting/surface/rhythm/breathing/effort).
- Tie each suggestion explicitly to Layer Z.

✅ SELF‑CHECK before output:
- No sport/tool names.
- Each suggestion ≥ 6 useful sentences and includes all six items.

🎯 Return exactly three «movement experiences»:

1) Core Identity:
   • Scene: ...
   • Inner Sensation: ...
   • Why you (Layer Z): ...
   • Practical Fit: ...
   • First Week: ...
   • Progress Markers: ...

2) Practical Alternative:
   • Scene: ...
   • Inner Sensation: ...
   • Why you (Layer Z): ...
   • Practical Fit: ...
   • First Week: ...
   • Progress Markers: ...

3) Creative/Mix:
   • Scene: ...
   • Inner Sensation: ...
   • Why you (Layer Z): ...
   • Practical Fit: ...
   • First Week: ...
   • Progress Markers: ...
"""
    return prompt


# ------------------------------
# [3] (اختياري) برومبت واضح للهوية بلا أسماء لاستخدامات أخرى
# ------------------------------
def generate_main_prompt_identity(analysis, answers, personality, lang="العربية"):
    """
    نسخة مطابقة لفلسفة "هوية بلا أسماء"، مفيدة إذا احتجت استدعاءً صريحًا من ملفات ثانية.
    """
    return generate_main_prompt(analysis, answers, personality, lang)
