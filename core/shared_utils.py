# core/shared_utils.py

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
        for k, v in answers.items():
            prompt += f"- {k}: {v}\n"

        prompt += f"""

📊 تقييم المستخدم للتوصيات السابقة:
{ratings}

📌 التوصيات الثلاثة التي قُدمت سابقًا:
1. {previous_recommendation[0] if len(previous_recommendation) > 0 else "—"}
2. {previous_recommendation[1] if len(previous_recommendation) > 1 else "—"}
3. {previous_recommendation[2] if len(previous_recommendation) > 2 else "—"}

⚠ قواعد صارمة:
- لا تذكر أسماء رياضات (مثل: جري، سباحة، كرة… إلخ). إن انزلق اسم، استبدله فورًا بـ "—" وقدّم وصفًا حسّيًا بديلًا.
- استخدم لغة حسّية تصف: المكان/السطح/الإيقاع/التنفس/نوع الجهد.
- اربط التوصية مباشرةً بـ Layer Z (لماذا أنت؟).
- اعطِ خطة للأسبوع الأول (٣ خطوات عملية واضحة).
- اعطِ مؤشرات تقدّم محسوسة خلال 2–4 أسابيع.

🎯 المطلوب الآن:
بناءً على كل ما سبق، أعطني *توصية أعمق وأصدق* بصيغة مقطع واحد بهذا القالب (من غير أسماء رياضات):
• المشهد: ...
• الإحساس الداخلي: ...
• لماذا أنت (Layer Z): ...
• الملاءمة العملية: (الزمن/المكان/التكلفة/الأمان) ...
• أول أسبوع: ...
• مؤشرات التقدم: ...

- كن ذكيًا، واقعيًا، وعاطفيًا. لا تكرر مضمون التوصيات السابقة، ولا تلمّح لأسمائها.
"""
    else:
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
        for k, v in answers.items():
            prompt += f"- {k}: {v}\n"

        prompt += f"""

📊 User's Ratings on Previous Recommendations:
{ratings}

📌 Previous Three Recommendations:
1. {previous_recommendation[0] if len(previous_recommendation) > 0 else "—"}
2. {previous_recommendation[1] if len(previous_recommendation) > 1 else "—"}
3. {previous_recommendation[2] if len(previous_recommendation) > 2 else "—"}

⚠ Hard Rules:
- Do NOT name any sports. If a sport name slips, replace it with "—" and provide a sensory description instead.
- Use sensory language: setting/surface/rhythm/breathing/type of effort.
- Explicitly tie the rationale to Layer Z (Why you?).
- Provide a First Week plan (3 concrete steps).
- Provide progress markers to notice within 2–4 weeks.

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
    تُستخدم لتوليد 3 توصيات رئيسية. تم تحويلها لوضع "هوية بلا أسماء".
    على الواجهة سيتم تنسيق المخرجات، لكن هنا نفرض اللغة والقواعد.
    """
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
        for k, v in answers.items():
            prompt += f"- {k}: {v}\n"

        prompt += """

⚠ قواعد صارمة:
- لا تذكر أسماء رياضات أبدًا. إن انزلق اسم، استبدله بـ "—" مع وصف حسّي بديل.
- استخدم لغة حسّية: المكان/السطح/الإيقاع/التنفس/نوع الجهد.
- اربط كل توصية بـ Layer Z.
- قدّم 3 توصيات دائمًا بهذا القالب:

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
        for k, v in answers.items():
            prompt += f"- {k}: {v}\n"

        prompt += """

⚠ Hard Rules:
- Absolutely NO sport names. If a sport name appears, replace it with "—" and describe the experience instead.
- Use sensory language: setting/surface/rhythm/breathing/type of effort.
- Tie each suggestion to Layer Z.
- Return exactly three suggestions using this template:

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
