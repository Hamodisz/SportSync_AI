import os
import csv
import json
from datetime import datetime

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141

from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
from core.chat_personality import BASE_PERSONALITY  # 🧠 الملف الثابت (أو بديله الديناميكي لاحقًا)

# 🗂 المسارات
CSV_PATH = "data/user_sessions.csv"
OUTPUT_PATH = "data/weekly_analysis.json"


# ---------------------------------------
# 📥 قراءة بيانات المستخدمين من CSV
# ---------------------------------------
def read_user_sessions():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


# ---------------------------------------
# 🧠 تحليل مستخدم واحد
# ---------------------------------------
def analyze_user(user):
    # 📌 نص موحّد لتحليل جميع الطبقات
    full_text = ' '.join([user.get(f'q{i+1}', '') for i in range(20)]) + ' ' + user.get('custom_input', '')

    # 🧬 تحليل الطبقات
    traits = {
        "traits_1_40": apply_layers_1_40(full_text),
        "traits_41_80": apply_layers_41_80(full_text),
        "traits_81_100": apply_layers_81_100(full_text),
        "traits_101_141": apply_layers_101_141(full_text),
    }

    # 🧭 تحليل المحركات الصامتة (Layer Z)
    try:
        silent_drivers = analyze_silent_drivers(answers=user, lang="العربية")
    except Exception as e:
        silent_drivers = [f"⚠ خطأ أثناء تحليل المحركات الصامتة: {str(e)}"]

    # 🧠 تجميع التحليل الكامل
    analysis = {
        **traits,
        "silent_drivers": silent_drivers,
        "base_personality": BASE_PERSONALITY,
    }

    return {
        "user_id": user.get("user_id", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis
    }


# ---------------------------------------
# 🚀 تنفيذ التحليل الأسبوعي الكامل
# ---------------------------------------
def run_weekly_analysis():
    users = read_user_sessions()
    results = []

    print(f"🔍 جاري تحليل {len(users)} مستخدم...")

    for user in users:
        try:
            result = analyze_user(user)
            results.append(result)
        except Exception as e:
            print(f"❌ خطأ مع المستخدم {user.get('user_id', 'unknown')}: {e}")

    with open(OUTPUT_PATH, mode='w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ تم حفظ نتائج التحليل الأسبوعي في {OUTPUT_PATH}")


# ---------------------------------------
# 🔁 نقطة تشغيل مستقلة
# ---------------------------------------
if _name_ == "_main_":
    run_weekly_analysis()