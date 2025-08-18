# -- coding: utf-8 --
"""
core/answers_encoder.py
-----------------------
طبقة ترميز (Encoder) لتحويل إجابات الكويز إلى بروفايل مضغوط قابل للاستخدام
في البرومبت والتحليل السريع.

- تعمل مع هيكل إجاباتك الحالي:
  answers = { "q1": {"question": "...", "answer": ["...", "..."]}, ... }
- تدعم العربية والإنجليزية تلقائيًا.
- تعطي درجات 0-10 لأبعاد: adrenaline, tactical, solo, social, novelty, mastery,
  sensory_seeking, discipline, structure, outdoor, indoor, risk_tolerance, equipment_affinity
- وتستنتج تفضيلات عملية: time_block, budget_hint, environment_pref
- ترجع كائن بروفايل + إشارات نصية قصيرة تلائم البرومبت.

طريقة الاستخدام النموذجية داخل backend_gpt.py:
    from core.answers_encoder import encode_answers
    profile = encode_answers(answers, lang)
    analysis["encoded_profile"] = profile
"""

from _future_ import annotations
import re
from typing import Dict, Any, List, Union

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

def _is_arabic_text(s: str) -> bool:
    return bool(_ARABIC_RE.search(s or ""))

def _tolist(x: Union[str, List[str], None]) -> List[str]:
    if x is None: return []
    if isinstance(x, list): return [str(i) for i in x]
    return [str(x)]

# -----------------------------
# معاجم كلمات بسيطة (ar/en)
# -----------------------------
KW = {
    "adrenaline": [
        # AR
        "مجازفة","خطر","اندفاع","أدرينالين","سرعة","قتال","انقضاض","مواجهة",
        # EN
        "adrenaline","thrill","risk","danger","rush","fast","combat","spar","chase","parkour","extreme"
    ],
    "tactical": [
        "تكتيك","تخطيط","تمويه","استراتيجية","ذكاء",
        "tactic","tactical","strategy","stealth","plan","analyze","analysis","mind game"
    ],
    "solo": [
        "لوحدي","فردي","انفرادي","وحيد",
        "solo","alone","individual"
    ],
    "social": [
        "مجموعة","فريق","جماعي","مع ناس","صديق","شريك",
        "group","team","with people","partner","buddy","coach"
    ],
    "novelty": [
        "اكتشاف","تجربة جديدة","شيء جديد","غير معتاد","ملل من التكرار",
        "novel","novelty","new","discovery","explore","bored","variety","change"
    ],
    "mastery": [
        "إتقان","عمق","صقل","ثبات","روتين","تحسين تدريجي",
        "mastery","master","depth","polish","drill","routine","incremental"
    ],
    "sensory": [
        "تنفّس","إيقاع","توتر","استرخاء","دفء","برودة","توازن","نبض","عرق","شد","مرونة","هدوء","تركيز","تدفّق","انسجام","ثقل","خفة",
        "breath","breathing","rhythm","tension","relax","warmth","cold","balance","pulse","sweat","stretch","calm","focus","flow","harmony","heavy","light"
    ],
    "discipline": [
        "انضباط","التزام","خطة","روتين","جدول",
        "discipline","consistency","commitment","plan","schedule","routine"
    ],
    "structure": [
        "خطة واضحة","برنامج","تعليمات","مراحل","قياس",
        "structured","program","instructions","phases","measure"
    ],
    "outdoor": [
        "خارج","هواء طلق","مسار","طبيعة","شمس","مضمار",
        "outdoor","outside","trail","nature","sun","track","park"
    ],
    "indoor": [
        "داخل","بيت","صالة","نادي","غرفة",
        "indoor","home","gym","room","studio"
    ],
    "risk": [
        "خطر","مخاطرة","اندفاع","سريع",
        "risk","danger","rush","fast","aggressive"
    ],
    "equipment": [
        "أداة","معدات","جهاز","الكترونية","سلاح",
        "equipment","gear","device","gadget","tool","weapon"
    ],
    "budget_low": [
        "صفر","مجاني","ميزانية قليلة","بدون تكلفة","قليل",
        "free","zero","low budget","cheap","no cost","minimal"
    ],
    "time_short": [
        "10","15","20","قصير","سريع",
        "short","10 min","15 min","20 min","quick"
    ],
    "calm_restore": [
        "هدوء","تنفّس","استعادة","صفاء","إعادة ضبط","راحة",
        "calm","breath","restore","reset","mindful","relax","recovery"
    ],
    "vr_like": [
        "واقع افتراضي","VR","افتراضي","محاكاة",
        "vr","virtual","simulation","immersive"
    ],
}

def _score_text(blob: str, keys: List[str]) -> int:
    blob_low = (blob or "").lower()
    score = 0
    for k in keys:
        if k.lower() in blob_low:
            score += 1
    return score

def _extract_all_text(answers: Dict[str, Any]) -> str:
    parts: List[str] = []
    for k, v in (answers or {}).items():
        if isinstance(v, dict):
            parts.append(str(v.get("question", "")))
            ans = v.get("answer", "")
            if isinstance(ans, list):
                parts.extend([str(i) for i in ans])
            else:
                parts.append(str(ans))
        else:
            parts.append(str(v))
    return "\n".join(parts)

# -----------------------------
# التحويل إلى بروفايل
# -----------------------------
def encode_answers(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    """
    يُرجع:
      {
        "scores": {adrenaline:0-10, tactical:0-10, ...},
        "prefs":  {time_block: short|medium|long, budget_hint: low|med|high, environment_pref: indoor|outdoor|mixed},
        "signals": [نصوص موجزة],
        "lang": "ar"|"en"
      }
    """
    # اجمع النص
    blob = _extract_all_text(answers)
    is_ar = _is_arabic_text(blob) if lang is None else (lang == "العربية")

    # نقاط أساسية
    s_adrenaline = _score_text(blob, KW["adrenaline"]) + _score_text(blob, KW["risk"])
    s_tactical   = _score_text(blob, KW["tactical"])
    s_solo       = _score_text(blob, KW["solo"])
    s_social     = _score_text(blob, KW["social"])
    s_novelty    = _score_text(blob, KW["novelty"])
    s_mastery    = _score_text(blob, KW["mastery"])
    s_sensory    = _score_text(blob, KW["sensory"]) + _score_text(blob, KW["calm_restore"])
    s_discipline = _score_text(blob, KW["discipline"]) + _score_text(blob, KW["structure"])
    s_outdoor    = _score_text(blob, KW["outdoor"])
    s_indoor     = _score_text(blob, KW["indoor"])
    s_risk_tol   = _score_text(blob, KW["risk"]) + _score_text(blob, KW["adrenaline"])
    s_gear       = _score_text(blob, KW["equipment"]) + (1 if "أداة إلكترونية" in blob or "electronic" in blob.lower() else 0)

    # زمن/ميزانية/بيئة
    time_block = "short" if _score_text(blob, KW["time_short"]) >= 1 else "medium"
    budget_hint = "low" if _score_text(blob, KW["budget_low"]) >= 1 else "med"
    if s_outdoor > s_indoor + 1:
        environment_pref = "outdoor"
    elif s_indoor > s_outdoor + 1:
        environment_pref = "indoor"
    else:
        environment_pref = "mixed"

    # قصّ الدرجات إلى 0..10
    def clamp10(x:int) -> int: return max(0, min(10, x))
    scores = {
        "adrenaline":      clamp10(s_adrenaline),
        "tactical":        clamp10(s_tactical),
        "solo":            clamp10(s_solo),
        "social":          clamp10(s_social),
        "novelty":         clamp10(s_novelty),
        "mastery":         clamp10(s_mastery),
        "sensory_seeking": clamp10(s_sensory),
        "discipline":      clamp10(s_discipline),
        "structure":       clamp10(s_discipline),   # synonymic view
        "outdoor":         clamp10(s_outdoor),
        "indoor":          clamp10(s_indoor),
        "risk_tolerance":  clamp10(s_risk_tol),
        "equipment_affinity": clamp10(s_gear),
    }

    # إشارات برومبت موجزة (تسند التوصيات)
    if is_ar:
        sig = []
        if scores["adrenaline"] >= 3: sig.append("يميل للأدرينالين/المجازفة")
        if scores["tactical"] >= 2:   sig.append("تفضيل تكتيك/تحليل")
        if scores["solo"] >= 2:       sig.append("يميل للنشاط الفردي")
        if scores["social"] >= 2:     sig.append("يستمتع بالتفاعل الاجتماعي")
        if scores["novelty"] >= 2:    sig.append("يكره التكرار ويحب التجديد")
        if scores["mastery"] >= 3:    sig.append("يركز على الإتقان التدريجي")
        if scores["sensory_seeking"] >= 3: sig.append("حساسية حسّية وتنظيم عصبي")
        if scores["discipline"] >= 3: sig.append("قابل للالتزام بخطة")
        sig.append(f"بيئة: { 'خارجي' if environment_pref=='outdoor' else 'داخلي' if environment_pref=='indoor' else 'هجين' }")
        sig.append(f"زمن الجلسة: {'قصير' if time_block=='short' else 'متوسط'}")
        sig.append(f"ميزانية: {'قليلة' if budget_hint=='low' else 'متوسطة'}")
    else:
        sig = []
        if scores["adrenaline"] >= 3: sig.append("adrenaline / risk seeking")
        if scores["tactical"] >= 2:   sig.append("tactical / analytical preference")
        if scores["solo"] >= 2:       sig.append("prefers solo")
        if scores["social"] >= 2:     sig.append("enjoys social/group")
        if scores["novelty"] >= 2:    sig.append("novelty seeking; dislikes repetition")
        if scores["mastery"] >= 3:    sig.append("focus on gradual mastery")
        if scores["sensory_seeking"] >= 3: sig.append("sensory regulation / mindful")
        if scores["discipline"] >= 3: sig.append("can follow a plan")
        sig.append(f"environment: {environment_pref}")
        sig.append(f"time block: {time_block}")
        sig.append(f"budget: {budget_hint}")

    prefs = {
        "time_block": time_block,
        "budget_hint": budget_hint,
        "environment_pref": environment_pref
    }

    return {
        "lang": ("العربية" if is_ar else "English"),
        "scores": scores,
        "prefs": prefs,
        "signals": sig,
        "vr_inclination": 1 if _score_text(blob, KW["vr_like"]) else 0
    }
