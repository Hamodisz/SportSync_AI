# -- coding: utf-8 --
"""
core/user_logger.py
-------------------
تسجيل تفاعلات وتحليلات المستخدم بصيغة JSON (append).
- متوافق مع الاستدعاءات القديمة: log_user_insight(user_id, content, event_type="...")
- يشتق تلقائيًا الحقول المهمة من المحتوى:
  lang, ratings, quality_flags, silent_drivers,
  encoded_profile.{scores->z_scores, prefs, signals, axes, z_markers, vr_inclination},
  ti_axis (إن وجد)، وعدد/مفاتيح الإجابات.

بيئة:
- INSIGHTS_LOG_PATH (اختياري) لتغيير مسار الملف.
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List

# 📍 مسار سجل التحليلات (قابل للضبط عبر متغير بيئي)
LOG_PATH = os.getenv("INSIGHTS_LOG_PATH", "data/insights_log.json")


# -------------------------------------------
# 🧼 تنظيف الكائنات من الدوال أو العناصر غير القابلة للتسلسل
# -------------------------------------------
def clean_for_logging(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: clean_for_logging(v) for k, v in obj.items() if not callable(v)}
    elif isinstance(obj, list):
        return [clean_for_logging(v) for v in obj if not callable(v)]
    elif callable(obj):
        return str(obj)
    return obj


# -------------------------------------------
# 🔎 مشتقات/تفريغ الحقول المهمة من المحتوى
# -------------------------------------------
def _extract_meta(content: Dict[str, Any]) -> Dict[str, Any]:
    """يستخرج حقول التحليل المهمة بشكل موحّد من content المتنوع."""
    meta: Dict[str, Any] = {}

    # اللغة
    meta["lang"] = content.get("language") or content.get("lang")

    # التقييمات والجودة
    meta["ratings"] = content.get("ratings")
    meta["quality_flags"] = content.get("quality_flags")

    # محركات Z
    analysis = content.get("analysis") or content.get("user_analysis") or {}
    meta["silent_drivers"] = (
        content.get("silent_drivers") or
        analysis.get("silent_drivers")
    )

    # بروفايل مُرمّز (answers_encoder)
    enc = (
        content.get("encoded_profile") or
        analysis.get("encoded_profile") or
        {}
    )

    # درجات Z (scores) + محاور (axes) + مؤشرات (z_markers)
    z_scores = enc.get("scores") or enc.get("z_scores")
    if z_scores is not None:
        meta["z_scores"] = z_scores

    if "axes" in enc:
        meta["z_axes"] = enc.get("axes")
        # إن كان فيه محور تقني↔حدسي مفصول باسم ti_axis
        if "ti_axis" in enc:
            meta["ti_axis"] = enc.get("ti_axis")
    else:
        # بعض النسخ قد تضع ti_axis مباشرة
        if "ti_axis" in enc:
            meta["ti_axis"] = enc.get("ti_axis")

    if "z_markers" in enc:
        meta["z_markers"] = enc.get("z_markers")

    # تفضيلات و"سيغنالات" البرومبت
    if "prefs" in enc or "preferences" in enc:
        meta["prefs"] = enc.get("prefs") or enc.get("preferences")
    if "signals" in enc:
        meta["signals"] = enc.get("signals")
    if "vr_inclination" in enc:
        meta["vr_inclination"] = enc.get("vr_inclination")

    # ملخّص بسيط عن الإجابات (عدّ، مفاتيح)
    answers = content.get("answers")
    if isinstance(answers, dict):
        meta["answers_count"] = len(answers)
        meta["answers_keys"] = list(answers.keys())[:50]  # لا نطوّل

    # آخر توصيات (اختياري للتتبّع)
    if "recommendations" in content:
        # خزّن الطول فقط لمنع تضخيم الملف
        try:
            meta["recommendations_count"] = len(content["recommendations"])
        except Exception:
            pass

    return clean_for_logging(meta)


# -------------------------------------------
# 📝 تسجيل التحليل أو الحدث في سجل المستخدمين
# -------------------------------------------
def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "user_insight") -> None:
    """
    يضيف سطرًا لسجل JSON. آمن على JSON الفارغ/الفاسد.
    - user_id: معرف المستخدم (نصي).
    - content: حمولة الحدث (سيتم تنظيفها).
    - event_type: نوع الحدث (string)، أمثلة:
        "initial_recommendation", "chat_interaction", "quality_check", ...
    """
    os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)

    clean_content = clean_for_logging(content or {})
    derived_meta = _extract_meta(clean_content)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "user_id": user_id,
        # حقول مشتقة لتسهيل التحليل دون الرجوع لكل الشجرة
        "meta": derived_meta,
        # المحتوى الأصلي (منظّف)
        "content": clean_content,
    }

    # append
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump([entry], f, ensure_ascii=False, indent=2)
        return

    # فتح + قراءة + إضافة + كتابة من البداية
    with open(LOG_PATH, "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                data = []
        except json.JSONDecodeError:
            data = []
        data.append(entry)
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()


# -------------------------------------------
# 📖 أدوات مساعدة اختيارية
# -------------------------------------------
def read_recent(n: int = 20) -> List[Dict[str, Any]]:
    """يرجع آخر n سجلات (إن وُجد الملف)."""
    if not os.path.exists(LOG_PATH):
        return []
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data[-n:]
    except Exception:
        return []


def count_by_event_type() -> Dict[str, int]:
    """إحصائية بسيطة بعدد السجلات لكل نوع حدث."""
    counts: Dict[str, int] = {}
    if not os.path.exists(LOG_PATH):
        return counts
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return counts
            for e in data:
                et = e.get("event_type", "unknown")
                counts[et] = counts.get(et, 0) + 1
    except Exception:
        pass
    return counts
