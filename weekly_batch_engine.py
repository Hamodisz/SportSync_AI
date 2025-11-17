import os
import csv
import json
from datetime import datetime

from src.analysis.analysis_layers_1_40 import apply_layers_1_40
from src.analysis.analysis_layers_41_80 import apply_layers_41_80
from src.analysis.analysis_layers_81_100 import apply_layers_81_100
from src.analysis.analysis_layers_101_141 import apply_layers_101_141
from src.analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
from src.utils.chat_personality import get_chat_personality

# Define BASE_PERSONALITY if needed
BASE_PERSONALITY = get_chat_personality()

CSV_PATH = "data/user_sessions.csv"
OUTPUT_PATH = "data/weekly_analysis.json"

def read_user_sessions():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def analyze_user(user):
    full_text = ' '.join(str(user.get(f"q{i+1}", "")) for i in range(20)) + ' ' + str(user.get("custom_input", ""))
    analysis = {
        "traits_1_40": apply_layers_1_40(full_text),
        "traits_41_80": apply_layers_41_80(full_text),
        "traits_81_100": apply_layers_81_100(full_text),
        "traits_101_141": apply_layers_101_141(full_text),
        "silent_drivers": analyze_silent_drivers(full_text),
        "base_personality": BASE_PERSONALITY,
    }
    return {
        "user_id": user.get("user_id", "unknown"),
        "analysis": analysis,
        "timestamp": datetime.utcnow().isoformat()
    }

def run_batch_analysis():
    sessions = read_user_sessions()
    all_results = [analyze_user(user) for user in sessions]
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"✅ تم حفظ تحليل {len(all_results)} مستخدم في {OUTPUT_PATH}")

if _name_ == "_main_":
    run_batch_analysis()