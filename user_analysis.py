# analysis/user_analysis.py
# -- coding: utf-8 --

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Union, Optional

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141
from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
from core.user_logger import log_user_insight  # ✅

DATA_DIR = "data/user_analysis"
os.makedirs(DATA_DIR, exist_ok=True)


# ======================
# Helpers
# ======================
def _answers_to_text(answers: Dict[str, Any]) -> str:
    parts: List[str] = []
    for v in (answers or {}).values():
        if isinstance(v, dict):
            parts.append(str(v.get("question", "")))
            a = v.get("answer", "")
            if isinstance(a, list):
                parts.extend([str(i) for i in a])
            else:
                parts.append(str(a))
        else:
            parts.append(str(v))
    return " ".join(str(x) for x in parts)

def _try_encode_profile(answers: Dict[str, Any], lang: str) -> Dict[str, Any]:
    # 1) لو فيه بروفايل مرسَّل جاهز
    for key in ("profile", "encoded_profile"):
        if isinstance(answers.get(key), dict):
            return answers[key]
    # 2) محاولة استخراج تلقائي إن وُجد الموديول
    try:
        from core.answers_encoder import encode_answers
        enc = encode_answers(answers, lang=lang)
        return {
            "scores": enc.get("scores", {}),
            "axes": enc.get("axes", {}),
            "preferences": enc.get("prefs", enc.get("preferences", {})),
            "z_markers": enc.get("z_markers", []),
            "signals": enc.get("signals", []),
            "vr_inclination": enc.get("vr_inclination", 0),
            "z_scores": enc.get("z_scores", {}),  # إن وُجدت
        }
    except Exception:
        return {}


# ======================
# واجهة موحّدة يستخدمها الـ backend والـ chat
# ======================
def apply_all_analysis_layers(text_or_answers: Union[str, Dict[str, Any]], lang: str = "العربية") -> Dict[str, Any]:
    """
    واجهة قياسية تُستخدم داخل dynamic_chat وغيرها.
    تقبل نصًا مجمّعًا أو answers dict وتُرجع كائن تحليل منظّم.
    """
    if isinstance(text_or_answers, dict):
        answers = text_or_answers
        full_text = _answers_to_text(answers)
    else:
        answers = {}
        full_text = str(text_or_answers or "")

    # استخرج البروفايل المُشفّر أولاً ليستفيد منه Layer-Z
    encoded = _try_encode_profile(answers, lang) if answers else {}

    # طبقات التحليل النصية
    traits: List[Any] = []
    traits += apply_layers_1_40(full_text)
    traits += apply_layers_41_80(full_text)
    traits += apply_layers_81_100(full_text)
    traits += apply_layers_101_141(full_text)

    # Layer-Z (تمرير encoded لزيادة الدقة)
    z_drivers: List[str] = []
    try:
        z_drivers = analyze_silent_drivers(answers=answers, lang=lang, encoded=encoded) if answers else []
    except Exception as e:
        z_drivers = [f"Layer-Z error: {e}"]

    # ملخّص سريع قابل للعرض
    quick_profile = " | ".join(str(t) for t in traits if isinstance(t, str))[:240]

    return {
        "lang": lang,
        "quick_profile": quick_profile or "fallback",
        "traits": traits,
        "silent_drivers": z_drivers,
        "encoded_profile": encoded,  # قد يكون {}
    }


# ======================
# توافُق خلفي + لوج وحفظ
# ======================
def analyze_user_from_answers(
    user_id_or_answers: Optional[Union[str, Dict[str, Any]]] = None,
    answers: Optional[Dict[str, Any]] = None,
    lang: str = "العربية",
    user_id: Optional[str] = None,
    **_  # ابتلاع أي براميترات زائدة (توافق مع نداءات قديمة)
) -> Dict[str, Any]:
    """
    توافُق مع استدعائين:
      - analyze_user_from_answers(answers=dict, lang=..)
      - analyze_user_from_answers(user_id='id', answers=dict, lang=..)
      - وكذلك يدعم analyze_user_from_answers(..., user_id='id') كـ keyword.
    تُرجع كائن تحليل منظّم (وليس قائمة فقط).
    """
    # تطبيع التواقيع
    if answers is None and isinstance(user_id_or_answers, dict):
        answers = user_id_or_answers
        if user_id is None:
            user_id = "session"
    else:
        if user_id is None:
            user_id = str(user_id_or_answers or "session")

    answers = answers or {}

    analysis = apply_all_analysis_layers(answers, lang=lang)

    # حفظ ملف JSON لكل مستخدم (إن توفر user_id)
    result_to_save = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "lang": lang,
        "traits": analysis.get("traits", []),
        "silent_drivers": analysis.get("silent_drivers", []),
        "encoded_profile": analysis.get("encoded_profile", {}),
        "quick_profile": analysis.get("quick_profile", ""),
    }

    path = os.path.join(DATA_DIR, f"{user_id}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result_to_save, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # لوج موحّد
    try:
        log_user_insight(user_id, result_to_save, event_type="user_analysis")
    except Exception:
        pass

    return analysis  # كائن منظّم


# ======================
# واجهات قديمة إن وُجدت
# ======================
def load_user_analysis(user_id: str) -> List[Any]:
    path = os.path.join(DATA_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("traits", [])
    except Exception:
        return []

def summarize_traits(traits: List[Any]) -> List[str]:
    if not traits:
        return []
    summarized: List[str] = []
    for t in traits:
        if isinstance(t, str):
            summarized.append(t.strip())
        elif isinstance(t, dict):
            try:
                summarized.append(json.dumps(t, ensure_ascii=False))
            except Exception:
                summarized.append(str(t))
    return summarized
