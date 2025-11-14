# core/layer_z_engine.py
# -- coding: utf-8 --
"""
Layer-Z Engine
==============

تحليل "الدوافع الصامتة" و"نوايا Z" من إجابات المستخدم بدون نماذج خارجية.
مصمّم ليكون خفيف وسريع وآمن، ويُرجّع إشارات مفيدة للباكند.

يوفّر الدوال:
- analyze_silent_drivers_combined(answers, lang="العربية") -> List[str]
- analyze_user_intent(answers, lang="العربية") -> List[str]

المخرجات المتوقع استعمالها من backend_gpt.py:
- الدوافع الصامتة قد تحتوي عبارات مثل:
  "إنجازات قصيرة", "نفور من التكرار", "تفضيل تحدّي ذهني",
  "تنظيم هدوء/تنفّس", "اندفاع/أدرينالين", "ميل للـ VR", "تفضيل فردي", "تفضيل جماعي"

- نوايا Z يجب أن تكون من المجموعة:
  ["VR","تخفّي","ألغاز/خداع","دقة/تصويب","قتالي","فردي","جماعي","هدوء/تنفّس","أدرينالين"]

لا يعتمد على مكتبات خارج الـ stdlib.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

# ========= Utilities: Arabic normalization & safe text extraction =========

_AR_DIAC = r"[ًٌٍَُِّْـ]"
_AR_DIAC_RE = re.compile(_AR_DIAC)

def _normalize_ar(t: str) -> str:
    if not t:
        return ""
    s = str(t)
    s = _AR_DIAC_RE.sub("", s)
    s = (s
         .replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
         .replace("ؤ", "و").replace("ئ", "ي")
         .replace("ة", "ه").replace("ى", "ي"))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _norm_text(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, (int, float, bool)):
        return str(val)
    if isinstance(val, (list, tuple, set)):
        flat: List[str] = []
        for x in val:
            if isinstance(x, (list, tuple, set)):
                flat.extend(map(str, x))
            else:
                flat.append(str(x))
        return "، ".join([s.strip() for s in flat if s and str(s).strip()])
    if isinstance(val, dict):
        for k in ("answer", "text", "desc", "value", "label", "title"):
            if k in val and isinstance(val[k], str):
                return val[k]
        try:
            return json.dumps(val, ensure_ascii=False)
        except Exception:
            return str(val)
    return str(val)

def _flatten_answers_blob(answers: Dict[str, Any]) -> Tuple[str, str]:
    """
    يرجّع (blob_lower, blob_norm_ar_lower)
    """
    parts: List[str] = []
    for v in (answers or {}).values():
        parts.append(_norm_text(v))
    blob = " ".join([p for p in parts if p])
    blob_l = blob.lower()
    blob_n = _normalize_ar(blob_l).lower()
    return blob_l, blob_n

def _lang_key(lang: str) -> str:
    return "ar" if (lang or "").startswith("الع") else "en"

# ========= Keyword banks =========

KW = {
    "ar": {
        "vr": ["vr", "واقع افتراضي", "نظاره", "خوذه", "سماعة رأس", "هيدسيت"],
        "stealth": ["تخفي", "ظل", "كمين", "تسلل", "غير مرئي"],
        "puzzles": ["لغز", "الغاز", "خدعه", "رمز", "تحليل", "تفكيك"],
        "precision": ["دقه", "تصويب", "نشان", "زاويه", "تثبيت نظر", "محاذاه"],
        "combat": ["قتال", "اشتباك", "مبارزه", "نزال", "صدام"],
        "calm": ["هدوء", "تنفس", "سكون", "استرخاء", "صفاء"],
        "adren": ["اندفاع", "حماس", "سريع", "مخاطره", "اثاره", "ادرينالين"],
        "solo": ["فردي", "لوحدي", "وحدي"],
        "team": ["جماعي", "فريق", "شريك", "تعاوني"],
        "repetition_aversion": ["تكرار ممل", "ملل", "نفور من التكرار", "روتين"],
        "quick_wins": ["سريع", "فوز سريع", "نتائج سريعه", "انجازات قصيره", "قصيره الاجل"],
        "mental": ["ذهني", "تفكير", "عقلي", "تحليلي", "ذكاء"],
        "anxiety": ["قلق", "توتر شديد", "مخاوف", "رهاب", "خوف"],
    },
    "en": {
        "vr": ["vr", "virtual reality", "headset", "hmd"],
        "stealth": ["stealth", "ambush", "shadow", "sneak", "undetected"],
        "puzzles": ["puzzle", "riddle", "feint", "trap", "cipher"],
        "precision": ["precision", "aim", "nock", "steady gaze", "alignment"],
        "combat": ["combat", "spar", "engage", "fight"],
        "calm": ["calm", "breath", "slow", "relax", "stillness", "settle"],
        "adren": ["adrenaline", "rush", "fast", "risk", "hype", "burst"],
        "solo": ["solo", "alone", "individual"],
        "team": ["team", "group", "partner", "co-op"],
        "repetition_aversion": ["bored", "repetitive", "routine", "hate repetition"],
        "quick_wins": ["quick win", "fast results", "short wins", "short-term"],
        "mental": ["mental", "cognitive", "tactical", "analytical", "brainy"],
        "anxiety": ["anxiety", "nervous", "phobia", "fear", "high stress"],
    },
}

# ========= Scoring helpers =========

def _any_kw(blob_l: str, blob_n: str, keys: List[str]) -> bool:
    if not keys:
        return False
    for k in keys:
        k_l = k.lower()
        if k_l in blob_l or _normalize_ar(k).lower() in blob_n:
            return True
    return False

def _score_from_kw(blob_l: str, blob_n: str, keys: List[str], weight: float = 1.0) -> float:
    return weight if _any_kw(blob_l, blob_n, keys) else 0.0

# ========= Public: Z-intent =========

def analyze_user_intent(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
    """
    يحدّد نوايا Z بناءً على كلمات مفتاحية واضحة.
    يَعِد بقيم ضمن المجموعة المتوقعة في الباكند.
    """
    bank = KW[_lang_key(lang)]
    blob_l, blob_n = _flatten_answers_blob(answers)

    intents: List[str] = []

    if _any_kw(blob_l, blob_n, bank["vr"]):
        intents.append("VR")
    if _any_kw(blob_l, blob_n, bank["stealth"]):
        intents.append("تخفّي")
    if _any_kw(blob_l, blob_n, bank["puzzles"]):
        intents.append("ألغاز/خداع")
    if _any_kw(blob_l, blob_n, bank["precision"]):
        intents.append("دقة/تصويب")
    if _any_kw(blob_l, blob_n, bank["combat"]):
        intents.append("قتالي")
    if _any_kw(blob_l, blob_n, bank["solo"]):
        intents.append("فردي")
    if _any_kw(blob_l, blob_n, bank["team"]):
        intents.append("جماعي")
    if _any_kw(blob_l, blob_n, bank["calm"]):
        intents.append("هدوء/تنفّس")
    if _any_kw(blob_l, blob_n, bank["adren"]):
        intents.append("أدرينالين")

    # إزالة التكرار مع الحفاظ على الترتيب
    seen = set()
    out: List[str] = []
    for it in intents:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out

# ========= Public: Silent drivers (combined) =========

def analyze_silent_drivers_combined(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
    """
    يحسب دوافع/ميول صامتة عبر نقاط بسيطة (بدون ML).
    يرجّع قائمة عبارات عربية مفهومة للباكند.

    أمثلة مخرجات:
    - "إنجازات قصيرة"
    - "نفور من التكرار"
    - "تفضيل تحدّي ذهني"
    - "تنظيم هدوء/تنفّس"
    - "اندفاع/أدرينالين"
    - "ميل للـ VR"
    - "تفضيل فردي"
    - "تفضيل جماعي"
    """
    bank = KW[_lang_key(lang)]
    blob_l, blob_n = _flatten_answers_blob(answers)

    # نقاط أساسية
    score_quick = _score_from_kw(blob_l, blob_n, bank["quick_wins"], 1.0)
    score_repav = _score_from_kw(blob_l, blob_n, bank["repetition_aversion"], 1.0)
    score_mental= _score_from_kw(blob_l, blob_n, bank["mental"], 1.0)
    score_calm  = _score_from_kw(blob_l, blob_n, bank["calm"], 1.0)
    score_adren = _score_from_kw(blob_l, blob_n, bank["adren"], 1.0)
    score_vr    = _score_from_kw(blob_l, blob_n, bank["vr"], 1.0)
    score_solo  = _score_from_kw(blob_l, blob_n, bank["solo"], 1.0)
    score_team  = _score_from_kw(blob_l, blob_n, bank["team"], 1.0)
    score_anx   = _score_from_kw(blob_l, blob_n, bank["anxiety"], 1.0)
    score_prec  = _score_from_kw(blob_l, blob_n, bank["precision"], 0.6)
    score_puzz  = _score_from_kw(blob_l, blob_n, bank["puzzles"], 0.6)
    score_stlh  = _score_from_kw(blob_l, blob_n, bank["stealth"], 0.6)
    score_comb  = _score_from_kw(blob_l, blob_n, bank["combat"], 0.6)

    # تحويل النقاط إلى عبارات عربية متوقعة
    drivers: List[Tuple[float, str]] = []

    if score_quick:
        drivers.append((score_quick, "إنجازات قصيرة"))
    if score_repav:
        drivers.append((score_repav, "نفور من التكرار"))
    if score_mental or score_puzz or score_prec:
        # وجود واحدة من (ذهني/ألغاز/دقة) يكفي لإضافة هذا الدافع
        drivers.append((max(score_mental, score_puzz, score_prec), "تفضيل تحدّي ذهني"))
    if score_calm:
        drivers.append((score_calm, "تنظيم هدوء/تنفّس"))
    if score_adren:
        drivers.append((score_adren, "اندفاع/أدرينالين"))
    if score_vr:
        drivers.append((score_vr, "ميل للـ VR"))
    if score_solo and (score_solo >= score_team):
        drivers.append((score_solo, "تفضيل فردي"))
    if score_team and (score_team > score_solo):
        drivers.append((score_team, "تفضيل جماعي"))
    if score_anx:
        # قد يستخدمها الباكند لحظر high-risk عبر GUARDS
        drivers.append((score_anx, "حساسية توتر/قلق"))

    # إشارات ناعمة إضافية (تعطي وزن بسيط؛ لا تغيّر المعنى الأساسي)
    soft_additions: List[Tuple[float, str]] = []
    if score_stlh:
        soft_additions.append((score_stlh, "ميول تكتيكي/تخفّي"))
    if score_comb:
        soft_additions.append((score_comb, "ميول قتالي (تكتيكي)"))
    if soft_additions:
        drivers.extend(soft_additions)

    # ترتيب وإزالة المكرّر
    drivers.sort(key=lambda x: x[0], reverse=True)
    seen: set = set()
    ordered: List[str] = []
    for _, label in drivers:
        if label not in seen:
            seen.add(label)
            ordered.append(label)

    # حدّ أقصى معقول (لكن لا نقصّر عمداً—نحافظ على السياق)
    # إن أردت تقليلها، يمكنك قصّ القائمة من الباكند لاحقًا.
    return ordered


__all__ = [
    "analyze_silent_drivers_combined",
    "analyze_user_intent",
]
