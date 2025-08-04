import json
from content_studio.publishing_engine import export_video_package

def run_batch_generation(json_path, start_index=1):
    """
    توليد مجموعة فيديوهات دفعة واحدة من ملف JSON يحتوي على سكربتات.
    كل عنصر في JSON يجب أن يحتوي على: {"script": "نص السكربت"}
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON يجب أن يحتوي على قائمة من السكربتات.")

    for i, item in enumerate(data, start=start_index):
        script = item.get("script")
        if not script:
            print(f"❌ تخطّي عنصر رقم {i} لأنه لا يحتوي على سكربت.")
            continue

        try:
            export_video_package(script_text=script, index=i)
        except Exception as e:
            print(f"⚠ خطأ أثناء توليد الفيديو {i}: {e}")

if _name_ == "_main_":
    # 🟢 استبدل هذا بالمسار الصحيح لملف السكربتات
    run_batch_generation("data/video_scripts.json", start_index=1)
