import json
import os

# 📁 مجلد التخزين المؤقت
CACHE_DIR = "data/user_sessions_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# 🔑 توليد مسار الملف من المفتاح
def get_cache_path(key):
    return os.path.join(CACHE_DIR, f"{key}.json")

# -----------------------------------------
# ✅ [1] تحليل المستخدم
# -----------------------------------------
def get_cached_analysis(key):
    path = get_cache_path(key)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("analysis", "")
        except Exception:
            return ""
    return ""

def save_cached_analysis(key, analysis_data):
    path = get_cache_path(key)
    data = {"analysis": analysis_data}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------------------------
# ✅ [2] شخصية المدرب الذكي
# -----------------------------------------
def get_cached_personality(user_analysis, lang):
    key = f"{lang}_{hash(str(user_analysis))}"
    path = get_cache_path(key)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("personality", {})
        except Exception:
            return {}
    return {}

def save_cached_personality(key, personality_data):
    path = get_cache_path(key)
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    existing["personality"] = personality_data
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)