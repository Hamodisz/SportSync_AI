# agents/marketing/chapter_archiver.py

"""
يحفظ أي سكربت طويل تم توليده من الذكاء
في مجلد مخصص كفصل من "كتاب Sport Sync AI".
"""

import os
import json
from datetime import datetime

CHAPTERS_DIR = "data/longform_chapters"

def save_script_as_chapter(script: dict):
    """
    يحفظ السكربت داخل مجلد longform_chapters كملف JSON.
    يُستخدم لاحقًا لبناء كتاب شامل من كل الحلقات.

    Parameters:
    - script (dict): يحتوي على title, sections, hook, moat_signature, tone
    """
    if not os.path.exists(CHAPTERS_DIR):
        os.makedirs(CHAPTERS_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}{script['title'].replace(' ', '')}.json"
    path = os.path.join(CHAPTERS_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
