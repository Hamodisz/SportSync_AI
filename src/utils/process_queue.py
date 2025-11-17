import os
import json
import time
from src.core.backend_gpt import analyze_user_from_answers

PENDING_DIR = "data/pending_requests"
RESULTS_DIR = "data/ready_results"

def process_pending_requests():
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    files = [f for f in os.listdir(PENDING_DIR) if f.endswith(".json")]
    print(f"📦 Found {len(files)} pending requests.")

    for filename in files:
        path = os.path.join(PENDING_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_id = data["user_id"]
        lang = data.get("lang", "ar")
        answers = data["answers"]

        print(f"🔍 Analyzing: {user_id} ...")
        try:
            profile, recommendations = analyze_user_from_answers(
                answers=answers,
                lang=lang,
                user_id=user_id
            )

            result_data = {
                "user_id": user_id,
                "profile": profile,
                "recommendations": recommendations,
                "analyzed_at": time.time()
            }

            result_path = os.path.join(RESULTS_DIR, f"{user_id}.json")
            with open(result_path, "w", encoding="utf-8") as out_f:
                json.dump(result_data, out_f, ensure_ascii=False, indent=2)

            os.remove(path)
            print(f"✅ Done: {user_id}")
        except Exception as e:
            print(f"❌ Error processing {user_id}: {e}")

if _name_ == "_main_":
    process_pending_requests()
