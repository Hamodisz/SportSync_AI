import os
import json

RESULTS_DIR = "data/ready_results"

def check_result(user_id):
    path = os.path.join(RESULTS_DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
