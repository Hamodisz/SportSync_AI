import os
import json
from datetime import datetime

PENDING_DIR = "data/pending_requests"

def submit_to_queue(user_id, answers, lang="ar"):
    """
    يحفظ إجابات المستخدم في مجلد الانتظار ليتم تحليلها لاحقًا.
    """
    os.makedirs(PENDING_DIR, exist_ok=True)

    payload = {
        "user_id": user_id,
        "lang": lang,
        "answers": answers,
        "submitted_at": datetime.utcnow().isoformat()
    }

    filepath = os.path.join(PENDING_DIR, f"{user_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return filepath
