# analysis/layer_z_engine.py

def analyze_silent_drivers_combined(user_data, questions={}):
    """
    تحليل المحركات الصامتة (Layer Z) لربط النوايا الداخلية بالتوصيات الرياضية.
    """
    from analysis.user_analysis import summarize_traits  # ✅ استيراد داخلي لحل الاستيراد الدائري

    full_text = user_data.get("full_text", "")
    answers = questions or user_data.get("answers", {})

    results = {}

    # ❶ تحليل الذوبان في النشاط (flow state)
    if "Q1" in answers:
        q1 = answers["Q1"].lower()
        if "time" in q1 or "forget" in q1 or "focus" in q1:
            results["flow_trigger"] = "deep immersion"
        elif "friends" in q1:
            results["flow_trigger"] = "social connection"
        else:
            results["flow_trigger"] = "unknown"

    # ❷ تحليل النية الداخلية وراء الحماس
    if "Q2" in answers:
        q2 = answers["Q2"].lower()
        if "challenge" in q2:
            results["inner_drive"] = "overcome limits"
        elif "control" in q2 or "mastery" in q2:
            results["inner_drive"] = "skill mastery"
        else:
            results["inner_drive"] = "expression"

    # ❸ تحليل قرارك التلقائي في بيئة جديدة
    if "Q3" in answers:
        q3 = answers["Q3"].lower()
        if "ball" in q3 or "equipment" in q3:
            results["impulse"] = "object curiosity"
        elif "climb" in q3 or "move" in q3:
            results["impulse"] = "movement initiation"
        else:
            results["impulse"] = "observe first"

    # ❹ تحليل ترددات الانقطاع أو الملل
    if "Q5" in answers:
        q5 = answers["Q5"].lower()
        if "bored" in q5 or "routine" in q5:
            results["break_trigger"] = "lack of novelty"
        elif "injury" in q5 or "pain" in q5:
            results["break_trigger"] = "physical discomfort"
        else:
            results["break_trigger"] = "unclear motivation"

    # ❺ تحليل المتعة الخاصة المخفية
    if "Q6" in answers:
        q6 = answers["Q6"].lower()
        if "secret" in q6 or "no one knows" in q6:
            results["hidden_reward"] = "private validation"
        elif "accomplish" in q6 or "create" in q6:
            results["hidden_reward"] = "inner pride"
        else:
            results["hidden_reward"] = "uncategorized"

    return results
