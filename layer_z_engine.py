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
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

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



# ========= NEW: Structured scoring from JSON with explicit scores =========

def calculate_z_scores_from_questions(
    answers: Dict[str, Any],
    questions_file: Optional[str] = None,
    lang: str = "العربية"
) -> Dict[str, float]:
    """
    Calculate Z-axis scores from user answers using explicit scores in questions JSON.

    Args:
        answers: User answers dict like {q1: {answer: ["option text"]}, q2: ...}
        questions_file: Path to questions JSON file. If None, auto-detect based on lang
        lang: Language (العربية or English)

    Returns:
        Dict of Z-axis scores like {
            "calm_adrenaline": 0.5,
            "solo_group": -0.3,
            "sensory_sensitivity": 0.7,
            ...
        }
    """
    # Auto-detect questions file
    if questions_file is None:
        script_dir = Path(__file__).parent
        # Try v2 format first, then fallback to old format
        if lang.startswith("العربية") or lang == "ar":
            v2_file = script_dir / "arabic_questions_v2.json"
            sample_file = script_dir / "arabic_questions_v2_sample.json"
            old_file = script_dir / "arabic_questions.json"

            if v2_file.exists():
                questions_file = str(v2_file)
            elif sample_file.exists():
                questions_file = str(sample_file)
            else:
                questions_file = str(old_file)
        else:
            v2_file = script_dir / "english_questions_v2.json"
            old_file = script_dir / "english_questions.json"

            if v2_file.exists():
                questions_file = str(v2_file)
            else:
                questions_file = str(old_file)

    # Load questions
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except Exception as e:
        print(f"[Z-ENGINE] ⚠️ Failed to load questions from {questions_file}: {e}")
        return {}

    # Check format (v2 vs old)
    if not questions:
        return {}

    first_q = questions[0]
    is_v2_format = "options" in first_q  # v2 has "options" array with scores

    if not is_v2_format:
        # Old format - return empty dict (fallback to keyword-based analysis)
        print(f"[Z-ENGINE] ℹ️ Old format detected, use keyword-based analysis instead")
        return {}

    # Initialize Z-axis accumulators
    z_totals: Dict[str, float] = {}
    z_weights: Dict[str, float] = {}

    # Process each answer
    for q_key, answer_data in answers.items():
        if q_key.startswith("_"):
            continue  # Skip metadata

        # Find matching question
        question = None
        for q in questions:
            if q.get("key") == q_key:
                question = q
                break

        if not question:
            continue

        # Extract user's selected option(s)
        selected_texts = []
        if isinstance(answer_data, dict):
            answer_val = answer_data.get("answer", [])
            if isinstance(answer_val, list):
                selected_texts = answer_val
            elif isinstance(answer_val, str):
                selected_texts = [answer_val]
        elif isinstance(answer_data, str):
            selected_texts = [answer_data]
        elif isinstance(answer_data, list):
            selected_texts = answer_data

        if not selected_texts:
            continue

        # Get question weight
        q_weight = question.get("weight", 1)

        # Match selected text to options and accumulate scores
        options = question.get("options", [])
        for option in options:
            text_ar = option.get("text_ar", "")
            text_en = option.get("text_en", "")
            scores = option.get("scores", {})

            # Check if this option was selected
            is_selected = False
            for selected in selected_texts:
                selected_normalized = _normalize_ar(str(selected).lower())
                ar_normalized = _normalize_ar(text_ar.lower())
                en_normalized = text_en.lower()

                if (selected_normalized in ar_normalized or
                    ar_normalized in selected_normalized or
                    selected.lower() in en_normalized or
                    en_normalized in selected.lower()):
                    is_selected = True
                    break

            if is_selected:
                # Add scores to totals
                for axis, score in scores.items():
                    if axis not in z_totals:
                        z_totals[axis] = 0.0
                        z_weights[axis] = 0.0

                    z_totals[axis] += score * q_weight
                    z_weights[axis] += q_weight

    # Calculate weighted averages
    z_scores: Dict[str, float] = {}
    for axis in z_totals:
        if z_weights[axis] > 0:
            avg = z_totals[axis] / z_weights[axis]
            # Clamp to valid range
            if axis in ["sensory_sensitivity"]:  # Unipolar axes (0.0 to 1.0)
                z_scores[axis] = max(0.0, min(1.0, avg))
            else:  # Bipolar axes (-1.0 to 1.0)
                z_scores[axis] = max(-1.0, min(1.0, avg))

    print(f"[Z-ENGINE] ✅ Calculated {len(z_scores)} Z-axis scores from {len(answers)} answers")
    for axis, score in sorted(z_scores.items()):
        print(f"[Z-ENGINE]    {axis}: {score:+.2f}")

    return z_scores


__all__ = [
    "analyze_silent_drivers_combined",
    "analyze_user_intent",
    "calculate_z_scores_from_questions",
]
