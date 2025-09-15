# core/shared_utils.py
# -- coding: utf-8 --

# =========================================================
# قيود مشتركة لمنع السطحية ومنع ذكر أسماء الرياضات
# =========================================================

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

_GENERIC_AVOID = [
    "أي نشاط بدني مفيد","اختر ما يناسبك","ابدأ بأي شيء","جرّب أكثر من خيار",
    "لا يهم النوع","تحرك فقط","نشاط عام","رياضة عامة","أنت تعرف ما يناسبك"
]

_SENSORY_TOKENS_AR = [
    "تنفّس","إيقاع","توتّر","استرخاء","دفء","برودة","توازن","نبض",
    "تعرّق","شدّ","مرونة","هدوء","تركيز","تدفّق","انسجام","ثِقل","خِفّة",
    "إحساس","موجة","امتداد","حرق لطيف","صفاء","تماسك"
]

# =========================================================
# أدوات مساعدة صغيرة لحقن محاور Z إن وُجدت
# =========================================================
def _axes_brief(analysis, lang="العربية"):
    ep = analysis.get("encoded_profile", {}) if isinstance(analysis, dict) else {}
    axes = ep.get("axes", analysis.get("z_axes", {})) if isinstance(analysis, dict) else {}
    markers = ep.get("z_markers") or ep.get("signals") or []
    scores = ep.get("scores", analysis.get("z_scores", {})) if isinstance(analysis, dict) else {}

    def fmt_axes(d):
        if not isinstance(d, dict) or not d:
            return "n/a"
        items = []
        for k, v in d.items():
            try:
                v = float(v)
            except Exception:
                pass
            items.append(f"{k}:{v}")
        return ", ".join(str(x) for x in items[:8])

    if lang == "العربية":
        return (
            f"محاور Z (مختصر): {fmt_axes(axes)}\n"
            + (f"مؤشرات: {', '.join(str(x) for x in markers[:6])}\n" if markers else "")
            + (f"أبرز الدرجات: {', '.join(str(f'{k}:{scores[k]}') for k in list(scores)[:5])}\n" if scores else "")
        ).strip()
    else:
        return (
            f"Z-axes brief: {fmt_axes(axes)}\n"
            + (f"Markers: {', '.join(str(x) for x in markers[:6])}\n" if markers else "")
            + (f"Top scores: {', '.join(str(f'{k}:{scores[k]}') for k in list(scores)[:5])}\n" if scores else "")
        ).strip()

# =========================================================
# (جديد) شخصية مدرّب ديناميكية لكي يختفي تحذير الاستيراد ويثبت الأسلوب
# =========================================================
def build_dynamic_personality(analysis, lang="العربية"):
    ep = analysis.get("encoded_profile", {}) if isinstance(analysis, dict) else {}
    axes = ep.get("axes", analysis.get("z_axes", {})) if isinstance(analysis, dict) else {}
    ti = axes.get("tech_intuition", 0) or axes.get("ti_axis", 0)
    calm = axes.get("calm_adrenaline", 0)
    solo = axes.get("solo_group", 0)

    # نبرة المتحدث مبنية على المحاور (تقريبي وبسيط)
    if calm >= 0.5:
        base_tone_ar = "هادئ، مطمئن، يركّز على الإحساس"
        base_tone_en = "calm, reassuring, sensation-first"
    elif calm <= -0.5:
        base_tone_ar = "نشِط، حازم، مباشر"
        base_tone_en = "energetic, firm, direct"
    else:
        base_tone_ar = "متزن، واضح، عملي"
        base_tone_en = "balanced, clear, practical"

    style_ar = "جُمل قصيرة، توجيه عملي، بدون تنظير"
    style_en = "short sentences, practical guidance, no fluff"

    if ti >= 0.5:   # ميول حدسي
        style_ar += "، يشجّع الاعتماد على الإحساس"
        style_en += ", leans on intuition cues"
    elif ti <= -0.5:  # ميول تقني
        style_ar += "، يوضح نقاط ضبط بسيطة"
        style_en += ", adds simple technique cues"

    name = "SportSync Coach"
    if lang == "العربية":
        return {
            "name": name,
            "tone": base_tone_ar,
            "style": style_ar,
            "philosophy": "هوية حركة بلا أسماء؛ الإنسان قبل الرياضة"
        }
    else:
        return {
            "name": name,
            "tone": base_tone_en,
            "style": style_en,
            "philosophy": "Name-less movement identity; human first"
        }

# =========================================================
# [1] برومبت المحادثة الديناميكية (بدون أسماء + بدون مكان/زمن/تكلفة/عدّات)
# =========================================================
def build_main_prompt(analysis, answers, personality, previous_recommendation, ratings, lang="العربية"):
    banned_ar = "، ".join(str(x) for x in _BANNED_SPORT_TERMS_AR)
    banned_en = ", ".join(str(x) for x in _BANNED_SPORT_TERMS_EN)
    avoid = "، ".join(str(x) for x in _GENERIC_AVOID)
    sensory = "، ".join(str(x) for x in _SENSORY_TOKENS_AR)
    axes_context = _axes_brief(analysis, lang)

    if lang == "العربية":
        prompt = f"""👤 تحليل المستخدم (مختصر):
{analysis.get('quick_profile','fallback')}

{('🧭 ' + axes_context) if axes_context else ''}

🧠 ملف المدرب:
الاسم: {personality.get('name')}
النبرة: {personality.get('tone')}
الأسلوب: {personality.get('style')}
الفلسفة: {personality.get('philosophy')}

📝 ملخص إجابات المستخدم (مضغوط للمرجع):
"""
        for k, v in (answers or {}).items():
            if isinstance(v, dict):
                prompt += f"- {v.get('question', k)}: {v.get('answer','')}\n"
            else:
                prompt += f"- {k}: {v}\n"

        prev = []
        for i in range(3):
            prev.append(previous_recommendation[i] if previous_recommendation and len(previous_recommendation) > i else "—")
        prompt += f"""

📊 تقييم المستخدم للتوصيات السابقة: {ratings}

📌 آخر 3 توصيات (للاطلاع فقط):
1. {prev[0]}
2. {prev[1]}
3. {prev[2]}

⚠ قواعد أسلوبية صارمة:
- ممنوع ذكر أسماء رياضات نهائيًا. محظورات أمثلة: [{banned_ar}] / [{banned_en}]
- إن انزلق اسم، استبدله فورًا بـ "—" وقدّم وصفًا حسّيًا بديلًا.
- لا تذكر المكان/الزمن/التكلفة/العدّات/الجولات/الدقائق.
- تجنّب العبارات السطحية: {avoid}
- لغة إنسانية بسيطة، جُمل قصيرة. كثّف الحسّيات (تذكير: {sensory}).
- اشرح ليش تناسبه ببساطة (لا تقل "Layer Z" لفظيًا).

✅ SELF-CHECK قبل الإخراج:
- لا أسماء رياضات أو أدوات، ولا مكان/زمن/تكلفة/عدّات.
- صياغة إنسانية موجّهة للمستخدم مباشرة.
- تضمين: المشهد، الإحساس الداخلي، لماذا أنت، أول أسبوع (نوعي)، مؤشرات تقدّم.

🎯 أعطني مقطع توصية واحد بهذه البنية (بدون أرقام):
• المشهد: ...
• الإحساس الداخلي: ...
• ليش تناسبك: ...
• أول أسبوع (نوعي): ...
• علامات تقدّم: ...
"""
    else:
        avoid_en = ", ".join(str(x) for x in _GENERIC_AVOID)
        prompt = f"""👤 User analysis (brief):
{analysis.get('quick_profile','fallback')}

{('🧭 ' + axes_context) if axes_context else ''}

🧠 Coach profile:
Name: {personality.get('name')}
Tone: {personality.get('tone')}
Style: {personality.get('style')}
Philosophy: {personality.get('philosophy')}

📝 Condensed answers (reference):
"""
        for k, v in (answers or {}).items():
            if isinstance(v, dict):
                prompt += f"- {v.get('question', k)}: {v.get('answer','')}\n"
            else:
                prompt += f"- {k}: {v}\n"

        prev = []
        for i in range(3):
            prev.append(previous_recommendation[i] if previous_recommendation and len(previous_recommendation) > i else "—")
        prompt += f"""

📊 Previous ratings: {ratings}

📌 Last 3 suggestions (for reference):
1. {prev[0]}
2. {prev[1]}
3. {prev[2]}

⚠ Hard style rules:
- Absolutely NO sport names. Banned examples: [{banned_en}]
- If any slips, replace with "—" and describe the sensation instead.
- Do NOT mention place/time/cost/reps/sets/minutes.
- Avoid generic phrases: {avoid_en}
- Human tone, short sentences. Increase sensory density.

✅ SELF-CHECK before output:
- No sport/tool names, no place/time/cost/reps.
- Human, directly addressing the user.
- Include: Scene, Inner sensation, Why you, First week (qualitative), Progress markers.

🎯 Return ONE recommendation block (no numbers):
• Scene: ...
• Inner sensation: ...
• Why it fits you: ...
• First week (qualitative): ...
• Progress markers: ...
"""
    return prompt


# =========================================================
# [2] برومبت 3 توصيات رئيسية للـ backend (بدون أسماء + بدون مكان/زمن/تكلفة/عدّات)
# =========================================================
def generate_main_prompt(analysis, answers, personality, lang="العربية"):
    banned_ar = "، ".join(str(x) for x in _BANNED_SPORT_TERMS_AR)
    banned_en = ", ".join(str(x) for x in _BANNED_SPORT_TERMS_EN)
    avoid = "، ".join(str(x) for x in _GENERIC_AVOID)
    sensory = "، ".join(str(x) for x in _SENSORY_TOKENS_AR)
    axes_context = _axes_brief(analysis, lang)

    if lang == "العربية":
        prompt = f"""🧠 تحليل المستخدم (مختصر): {analysis.get('quick_profile','fallback')}
{('🧭 ' + axes_context) if axes_context else ''}

👤 الملف النفسي للمدرب:
الاسم: {personality.get("name")}
النبرة: {personality.get("tone")}
الأسلوب: {personality.get("style")}
الفلسفة: {personality.get("philosophy")}

📝 إجابات المستخدم (للرجوع فقط، لا تعيدها نصًا):
"""
        for k, v in (answers or {}).items():
            if isinstance(v, dict):
                prompt += f"- {v.get('question', k)}: {v.get('answer','')}\n"
            else:
                prompt += f"- {k}: {v}\n"

        prompt += f"""

⚠ قواعد صارمة:
- ممنوع تمامًا ذكر أسماء الرياضات: [{banned_ar}] / [{banned_en}]
- لا مكان/زمن/تكلفة/عدّات/جولات/دقائق.
- تجنّب العبارات السطحية: {avoid}
- زد الكثافة الحسّية (تذكير: {sensory})
- علّل كل توصية ببساطة (ليش تناسبه).

✅ SELF-CHECK:
- صفر أسماء رياضية وأرقام زمن/عدّات.
- لكل توصية ≥ 6 جمل مفيدة وتتضمن العناصر المطلوبة.

🎯 أعطني ثلاث «تجارب حركة» بالضبط (JSON داخلي سيُبنى لاحقًا)، اكتب المحتوى النصي لهذه الحقول فقط:
1) الهوية الأساسية:
   • المشهد: ...
   • الإحساس الداخلي: ...
   • ليش تناسبك: ...
   • أول أسبوع (نوعي): ...
   • مؤشرات التقدم: ...

2) البديل الواقعي:
   • المشهد: ...
   • الإحساس الداخلي: ...
   • ليش تناسبك: ...
   • أول أسبوع (نوعي): ...
   • مؤشرات التقدم: ...

3) الابتكارية/المزيج:
   • المشهد: ...
   • الإحساس الداخلي: ...
   • ليش تناسبك: ...
   • أول أسبوع (نوعي): ...
   • مؤشرات التقدم: ...
"""
    else:
        avoid_en = ", ".join(str(x) for x in _GENERIC_AVOID)
        prompt = f"""🧠 User analysis (brief): {analysis.get('quick_profile','fallback')}
{('🧭 ' + axes_context) if axes_context else ''}

👤 Coach profile:
Name: {personality.get("name")}
Tone: {personality.get("tone")}
Style: {personality.get("style")}
Philosophy: {personality.get("philosophy")}

📝 User answers (for reference, do not echo verbatim):
"""
        for k, v in (answers or {}).items():
            if isinstance(v, dict):
                prompt += f"- {v.get('question', k)}: {v.get('answer','')}\n"
            else:
                prompt += f"- {k}: {v}\n"

        prompt += f"""

⚠ Hard rules:
- No sport names whatsoever: [{banned_en}]
- No place/time/cost/reps/sets/minutes.
- Avoid generic phrases: {avoid_en}
- Increase sensory density; explain simply why it fits.

✅ SELF-CHECK:
- Zero sport names and numeric session details.
- Each suggestion ≥ 6 meaningful sentences and includes the required parts.

🎯 Return exactly three «movement experiences». Write only the textual content for these keys:
1) Core identity:
   • Scene: ...
   • Inner sensation: ...
   • Why it fits you: ...
   • First week (qualitative): ...
   • Progress markers: ...

2) Practical alternative:
   • Scene: ...
   • Inner sensation: ...
   • Why it fits you: ...
   • First week (qualitative): ...
   • Progress markers: ...

3) Creative / mix:
   • Scene: ...
   • Inner sensation: ...
   • Why it fits you: ...
   • First week (qualitative): ...
   • Progress markers: ...
"""
    return prompt


# ------------------------------
# [3] نسخة مطابقة لفلسفة "هوية بلا أسماء"
# ------------------------------
def generate_main_prompt_identity(analysis, answers, personality, lang="العربية"):
    return generate_main_prompt(analysis, answers, personality, lang)
