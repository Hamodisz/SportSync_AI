# -- coding: utf-8 --
"""
core/recs/rules.py
------------------
قواعد/حراس النصوص (RegEx) كما هي من backend_gpt.py بدون اختصار:
- قائمة كلمات/عبارات تحظر ذكر أسماء الرياضات عند الحاجة.
- نمط العبارات الممنوعة (وقت/تكلفة/جولات/مكان مباشر).
- دوال: contains_blocked_name, mask_names, scrub_forbidden.

ملاحظات:
- لا يعتمد هذا الملف على إعدادات خارجية؛ تمرير السماح/المنع لأسماء الرياضات يكون
  عبر معامل الدالة mask_names(allow_sport_names=...).
- يعتمد على utilيات التطبيع والتقسيم من core/recs/text_ops.py.
"""

from __future__ import annotations

import re
from typing import List

from .text_ops import _normalize_ar, _split_sentences

# ========= Blocklist لأسماء الرياضات/الأنشطة =========
_BLOCKLIST = (
    r"(جري|ركض|سباحة|كرة|قدم|سلة|طائرة|تنس|ملاكمة|كاراتيه|كونغ فو|يوجا|يوغا|بيلاتس|رفع|أثقال|"
    r"تزلج|دراج|دراجة|ركوب|خيول|باركور|جودو|سكواش|بلياردو|جولف|كرة طائرة|كرة اليد|هوكي|"
    r"سباق|ماراثون|مصارعة|MMA|Boxing|Karate|Judo|Taekwondo|Soccer|Football|Basketball|Tennis|"
    r"Swim|Swimming|Running|Run|Cycle|Cycling|Bike|Biking|Yoga|Pilates|Rowing|Row|Skate|Skating|"
    r"Ski|Skiing|Climb|Climbing|Surf|Surfing|Golf|Volleyball|Handball|Hockey|Parkour|Wrestling)"
)
_name_re = re.compile(_BLOCKLIST, re.IGNORECASE)

# ========= نمط الجمل/المفردات الممنوعة (وقت/تكلفة/جولات/مكان مباشر) =========
_FORBIDDEN_SENT = re.compile(
    r"(\b\d+(\.\d+)?\s*(?:min|mins|minute|minutes|second|seconds|hour|hours|دقيقة|دقائق|ثانية|ثواني|ساعة|ساعات)\b|"
    r"(?:rep|reps|set|sets|تكرار|عدة|عدات|جولة|جولات|×)|"
    r"(?:تكلفة|ميزانية|cost|budget|ريال|دولار|\$|€)|"
    r"(?:بالبيت|في\s*البيت|قرب\s*المنزل|بالمنزل|في\s*النادي|في\s*الجيم|صالة|نادي|جيم|غرفة|ساحة|ملعب|حديقة|شاطئ|"
    r"طبيعة|خارجي(?:ة)?|داخل(?:ي|ية)?|outdoor|indoor|park|beach|gym|studio))",
    re.IGNORECASE
)

def contains_blocked_name(t: str) -> bool:
    """
    تحقّق إن كان النص يحتوي على اسم نشاط/رياضة محظور (مباشرًا أو بعد التطبيع العربي).
    """
    if not t:
        return False
    return bool(_name_re.search(t)) or bool(_name_re.search(_normalize_ar(t)))

def mask_names(t: str, allow_sport_names: bool = True) -> str:
    """
    إخفاء أسماء الرياضات إن كان allow_sport_names=False.
    - إن لم يُسمح: نستبدل التطابقات بشرطة طويلة — ،
      وإن فشل الاستبدال لكن لا زال يحتوي اسمًا محظورًا بعد التطبيع نرجعه كـ '—'.
    """
    if allow_sport_names:
        return t or ""
    s = t or ""
    s2 = _name_re.sub("—", s)
    if s2 == s and contains_blocked_name(s):
        s2 = "—"
    return s2

def scrub_forbidden(text: str) -> str:
    """
    إزالة الجُمل التي تحتوي على وقت/تكلفة/جولات/مكان مباشر باستخدام _FORBIDDEN_SENT.
    نُقسّم إلى جمل، ننقّي، ثم نعيد تركيبها مفصولة بـ '، '.
    """
    kept: List[str] = [
        s for s in _split_sentences(text) if not _FORBIDDEN_SENT.search(_normalize_ar(s))
    ]
    return "، ".join(kept).strip(" .،")
