# core/shared_utils.py

# ------------------------------
# [1] دالة توصية أعمق - للديناميكي
# ------------------------------
def build_main_prompt(analysis, answers, personality, previous_recommendation, ratings, lang="العربية"):
    if lang == "العربية":
        prompt = f"""👤 تحليل شخصية المستخدم:
{analysis}
"""

        if isinstance(analysis, dict) and "silent_drivers" in analysis:
            silent = analysis["silent_drivers"]
            if silent:
                prompt += "🧭 المحركات الصامتة:\n"
                for s in silent:
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

🎯 المطلوب الآن:
بناءً على كل ما سبق، اعطني توصية أعمق وأصدق. لا تكرر نفس التوصيات، ولا تذكر الرياضات الثلاثة السابقة. وجهه إلى شيء يلائم أعماقه ويحفز روحه. إذا لم تكن هناك رياضة حقيقية تناسبه، يمكنك اختراع أو دمج رياضة جديدة خصيصًا له.

- استخدم أسلوب إنساني، عاطفي، وغير مباشر.
- يجب أن تكون التوصية ذكية، واقعية، ومقنعة.
"""
    else:
        prompt = f"""👤 User Personality Analysis:
{analysis}
"""

        if isinstance(analysis, dict) and "silent_drivers" in analysis:
            silent = analysis["silent_drivers"]
            if silent:
                prompt += "🧭 Silent Drivers:\n"
                for s in silent:
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

🎯 Your task now:
Based on everything above, give a deeper, more meaningful sport suggestion.
Avoid repeating the same previous three recommendations.
If no real sport fits them perfectly, invent or hybridize one that does.

- Be emotionally intelligent and human.
- Make it realistic, innovative, and inspiring.
"""
    return prompt


# ------------------------------
# [2] دالة 3 توصيات رئيسية - للbackend
# ------------------------------
def generate_main_prompt(analysis, answers, personality, lang="العربية"):
    if lang == "العربية":
        prompt = f"""🧠 تحليل المستخدم:
{analysis}
"""

        if isinstance(analysis, dict) and "silent_drivers" in analysis:
            silent = analysis["silent_drivers"]
            if silent:
                prompt += "🧭 المحركات الصامتة:\n"
                for s in silent:
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

🎯 المطلوب الآن:
بناءً على كل ما سبق، أعطني 3 توصيات رياضية مفصلة بهذا الشكل:

1. التوصية رقم 1 (الأنسب عاطفيًا وواقعيًا)
2. التوصية رقم 2 (بديل واقعي جيد)
3. التوصية رقم 3 (رياضية مبتكرة أو مزيج مخصص)

- كل توصية يجب أن تكون مقنعة، ملهمة، وعاطفية.
- استخدم أسلوب بشري لا يشبه الآلة.
- لا تكرر نفس الرياضة في أكثر من توصية.
"""
    else:
        prompt = f"""🧠 User Analysis:
{analysis}
"""

        if isinstance(analysis, dict) and "silent_drivers" in analysis:
            silent = analysis["silent_drivers"]
            if silent:
                prompt += "🧭 Silent Drivers:\n"
                for s in silent:
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

🎯 Your task now:
Based on the above, give me 3 distinct sport suggestions formatted as:

1. Recommendation #1 (most emotionally and practically fitting)
2. Recommendation #2 (a realistic alternative)
3. Recommendation #3 (a creative or hybridized option)

- Make them inspiring, human, and non-repetitive.
- Each one should stand on its own as a smart, emotional recommendation.
"""
    return prompt