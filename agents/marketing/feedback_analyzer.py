# agents/marketing/feedback_analyzer.py

import json
from datetime import datetime
from core.user_logger import log_user_insight
from analysis.user_analysis import analyze_user_from_answers


def analyze_feedback(feedback_text, user_id=None, answers=None):
    """
    يحلل تعليقات الجمهور أو تقييماتهم ويستنتج منها نمط الاستجابة أو التفاعل.
    يمكن استخدام هذا التحليل لتحسين المحتوى أو فهم مدى تأثير الذكاء الرياضي.

    Parameters:
    - feedback_text (str): النص الكامل لتعليق أو تقييم المستخدم.
    - user_id (str, optional): معرف المستخدم.
    - answers (dict, optional): إجابات المستخدم الأصلية إن وُجدت.

    Returns:
    - dict: تحليل دلالي للعاطفة أو الاتجاه أو الاقتراحات المهمة.
    """
    result = {
        "sentiment": "neutral",
        "keywords": [],
        "suggestions": [],
        "raw_feedback": feedback_text,
        "analyzed_at": datetime.utcnow().isoformat()
    }

    if not feedback_text:
        return result

    # تحليل مبدئي بسيط باستخدام كلمات مفتاحية (يمكن تطويره لاحقًا باستخدام LLM)
    lowered = feedback_text.lower()
    if any(word in lowered for word in ["love", "great", "amazing", "useful"]):
        result["sentiment"] = "positive"
    elif any(word in lowered for word in ["hate", "bad", "boring", "useless", "not working"]):
        result["sentiment"] = "negative"
    else:
        result["sentiment"] = "neutral"

    # استخراج كلمات مهمة
    words = feedback_text.replace(".", "").replace(",", "").split()
    result["keywords"] = [word for word in words if len(word) > 4][:5]

    # لو فيه user_id نحفظ التحليل
    if user_id:
        log_user_insight({
            "type": "feedback_analysis",
            "user_id": user_id,
            "feedback": feedback_text,
            "sentiment": result["sentiment"],
            "keywords": result["keywords"],
            "timestamp": result["analyzed_at"]
        })

    return result
