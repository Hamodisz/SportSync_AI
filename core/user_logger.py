import os
import json
from datetime import datetime

# 📍 مسار سجل التحليلات
LOG_PATH = "data/insights_log.json"


# -------------------------------------------
# 🧼 تنظيف الكائنات من الدوال أو العناصر غير القابلة للتسلسل
# -------------------------------------------
def clean_for_logging(obj):
    if isinstance(obj, dict):
        return {k: clean_for_logging(v) for k, v in obj.items() if not callable(v)}
    elif isinstance(obj, list):
        return [clean_for_logging(v) for v in obj if not callable(v)]
    elif callable(obj):
        return str(obj)
    return obj


# -------------------------------------------
# 📝 تسجيل التحليل أو الحدث في سجل المستخدمين
# -------------------------------------------
def log_user_insight(user_id, content, event_type="user_insight"):
    os.makedirs("data", exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "content": clean_for_logging(content),
    }

    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump([entry], f, ensure_ascii=False, indent=2)
    else:
        with open(LOG_PATH, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(entry)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)