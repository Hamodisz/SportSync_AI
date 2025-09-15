# -- coding: utf-8 --
"""
analysis/layer_z_engine.py
--------------------------
- z_drivers_from_scores(z_scores): يحوّل محاور [-1..+1] إلى جُمل محركات Layer-Z أنيقة.
- analyze_silent_drivers_combined(answers, lang="العربية", encoded=None):
  يستخدم encoded["z_scores"] إن توفّر؛ وإلا يستنتج سريعًا من النص.
"""

from __future__ import annotations
from typing import Dict, List, Any
import re

_AR_RE = re.compile(r"[\u0600-\u06FF]")

def _is_ar(s: str) -> bool:
    return bool(_AR_RE.search(s or ""))

def z_drivers_from_scores(z_scores: Dict[str, float], lang: str = "العربية") -> List[str]:
    """
    z_scores مفاتيح متوقعة:
      technical_intuitive, control_freedom, repeat_variety, compete_enjoy,
      calm_adrenaline, solo_group, sensory_sensitivity
    القيم: -1..+1 (الموجب باتجاه الطرف الأول المذكور في الاسم).
    """
    if not isinstance(z_scores, dict):
        return []
    def gt(x, t=0.4):  return (x or 0) >= t
    def lt(x, t=-0.4): return (x or 0) <= t

    ar = (lang == "العربية")
    out: List[str] = []

    ti = z_scores.get("technical_intuitive", 0.0)
    if gt(ti):  out.append("ميل تقني دقيق" if ar else "Technical precision bias")
    elif lt(ti): out.append("ميل حدسي لحظي" if ar else "Intuitive/instinctive bias")

    cf = z_scores.get("control_freedom", 0.0)
    if gt(cf):  out.append("تفضيل السيطرة والبروتوكول" if ar else "Control/protocol preference")
    elif lt(cf): out.append("تفضيل الحرية والانسياب" if ar else "Freedom/flow preference")

    rv = z_scores.get("repeat_variety", 0.0)
    if gt(rv):  out.append("يرتاح للتكرار والإتقان" if ar else "Repetition/mastery comfort")
    elif lt(rv): out.append("يكره الرتابة ويبحث عن تنويع" if ar else "Variety/novelty seeking")

    ce = z_scores.get("compete_enjoy", 0.0)
    if gt(ce):  out.append("محفَّز بالمنافسة والتفوّق" if ar else "Competition/dominance driven")
    elif lt(ce): out.append("محفَّز بالمتعة والتجربة" if ar else "Enjoyment/experience driven")

    ca = z_scores.get("calm_adrenaline", 0.0)
    if gt(ca):  out.append("ينجذب للأدرينالين والاندفاع" if ar else "Adrenaline/thrill seeking")
    elif lt(ca): out.append("يميل للهدوء والتنظيم العصبي" if ar else "Calm/parasympathetic regulation")

    sg = z_scores.get("solo_group", 0.0)
    if gt(sg):  out.append("ميول فردية" if ar else "Solo-inclined")
    elif lt(sg): out.append("يستمتع بالجماعة" if ar else "Group-inclined")

    ss = z_scores.get("sensory_sensitivity", 0.0)
    if abs(ss) >= 0.5:
        out.append("حساسية حسّية مؤثّرة" if ar else "Notable sensory sensitivity")

    return out

def _quick_fallback_from_text(answers: Dict[str, Any], lang: str) -> List[str]:
    # استنتاجات بدائية لو ما توفر encoded
    joined = []
    for k, v in (answers or {}).items():
        if isinstance(v, dict):
            a = v.get("answer", "")
            if isinstance(a, list): joined.extend([str(i) for i in a])
            else: joined.append(str(a))
        else:
            joined.append(str(v))
    text = "\n".join(str(x) for x in joined).lower()
    ar = (lang == "العربية")

    out: List[str] = []
    if any(t in text for t in ["خطر","ادرينالين","اندفاع","risk","adrenaline","thrill"]):
        out.append("ينجذب للأدرينالين والاندفاع" if ar else "Adrenaline/thrill seeking")
    if any(t in text for t in ["تخطيط","تكتيك","plan","tactic","strategy","تحليل","analyz"]):
        out.append("تفضيل تكتيك/تحليل" if ar else "Tactical/analytical preference")
    if any(t in text for t in ["لوحدي","فردي","solo","alone"]):
        out.append("ميول فردية" if ar else "Solo-inclined")
    if any(t in text for t in ["مجموعة","فريق","group","team"]):
        out.append("يستمتع بالجماعة" if ar else "Group-inclined")
    if any(t in text for t in ["ملل","تنويع","variety","bored"]):
        out.append("يكره الرتابة ويبحث عن تنويع" if ar else "Variety/novelty seeking")
    if any(t in text for t in ["هدوء","تنفس","calm","breath","mindful"]):
        out.append("يميل للهدوء والتنظيم العصبي" if ar else "Calm/regulation seeking")
    return list(dict.fromkeys(out))  # إزالة التكرار

def analyze_silent_drivers_combined(
    answers: Dict[str, Any],
    lang: str = "العربية",
    encoded: Dict[str, Any] | None = None
) -> List[str]:
    """
    يعيد قائمة محركات Layer-Z النصية (مرتبة ومختصرة).
    يعطي أولوية لـ encoded['z_scores'] إن توفرت.
    """
    items: List[str] = []
    if isinstance(encoded, dict):
        zs = encoded.get("z_scores") or encoded.get("scores")  # احتياط
        if isinstance(zs, dict):
            items.extend(z_drivers_from_scores(zs, lang=lang))

    if not items:
        items.extend(_quick_fallback_from_text(answers, lang))

    # قص القائمة إلى 6 لئلا تثقل البرومبت
    return items[:6]
