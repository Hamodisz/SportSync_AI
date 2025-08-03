import json
from agents.marketing.content_creator import generate_content

# تحميل بيانات المستخدم من ملف JSON
with open("user_data.json", "r", encoding="utf-8") as f:
    user_data = json.load(f)

# توليد المحتوى بناءً على التحليل
results = generate_content(user_data, lang=user_data["lang"])

# عرض النتائج
print("\n=== المحتوى المُولد بواسطة وكيل Sport Sync ===\n")
for idx, post in enumerate(results, 1):
    print(f"\n📌 منشور رقم {idx}:\n{post}\n")
