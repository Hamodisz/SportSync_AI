# analysis/user_analysis.py

import os
import json
from datetime import datetime

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141
from core.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers  # ✅
from core.user_logger import log_user_insight  # ✅

DATA_DIR = "data/user_analysis"
os.makedirs(DATA_DIR, exist_ok=True)

# 🔍 التحليل الكامل للمستخدم
def analyze_user_from_answers(user_id: str, answers: dict, lang="العربية") -> list:
    full_text = ' '.join([str(v) for v in answers.values()])

    traits = []
    traits += apply_layers_1_40(full_text)
    traits += apply_layers_41_80(full_text)
    traits += apply_layers_81_100(full_text)
    traits += apply_layers_101_141(full_text)

    try:
        silent = analyze_silent_drivers(answers=answers, lang=lang)
        traits += silent
    except Exception as e:
        traits.append(f"❌ خطأ في تحليل Layer Z: {e}")

    # 🧠 حفظ التحليل
    result = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "lang": lang,
        "traits": traits
    }

    path = os.path.join(DATA_DIR, f"{user_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 🗂 لوق خاص
    log_user_insight(user_id, result, event_type="user_analysis")

    return traits

# 📥 استرجاع تحليل مستخدم سابق
def load_user_analysis(user_id: str) -> list:
    path = os.path.join(DATA_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("traits", [])