# core/chat_personality.py

import json
import os

MEMORY_PATH = "data/chat_memory.json"

# 🧠 تحميل أو إنشاء الذاكرة
def load_memory():
    if not os.path.exists(MEMORY_PATH):
        return {}
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 حفظ الذاكرة
def save_memory(memory):
    os.makedirs("data", exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# 🧠 استرجاع شخصية الذكاء
def get_chat_personality(user_id=None, lang="العربية"):
    memory = load_memory()

    if user_id and user_id in memory:
        return memory[user_id]

    # إذا لم توجد شخصية محفوظة، نرجع واحدة افتراضية حسب اللغة
    if lang == "العربية":
        return {
            "name": "المدرب نواة",
            "tone": "ذكي وعاطفي",
            "style": "تحليلي وإنساني",
            "philosophy": "الرياضة ليست نشاطًا بل مرآة للهوية. كل حركة تكشف دافعًا داخليًا، ومهمتي مساعدتك تكتشف رياضتك الحقيقية."
        }
    else:
        return {
            "name": "Coach Core",
            "tone": "Smart and empathetic",
            "style": "Analytical and human-centered",
            "philosophy": "Sport is not just an activity — it's a mirror of identity. Every move reveals a silent driver, and my role is to help you discover your true sport."
        }

# 🛠 تحديث الشخصية ببيانات جديدة
def update_chat_personality(user_id, lang=None, traits_summary=None):
    memory = load_memory()
    base = memory.get(user_id, get_chat_personality(lang=lang))

    if lang:
        base["lang"] = lang
    if traits_summary:
        base["last_traits"] = traits_summary

    memory[user_id] = base
    save_memory(memory)