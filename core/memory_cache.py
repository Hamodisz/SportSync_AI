# -- coding: utf-8 --
"""
core/memory_cache.py
--------------------
كاش بسيط/سريع لشخصية المدرب (persona) مع عدادات HIT/MISS وقياسات زمنية.

المزايا:
- مفتاح ثابت باستخدام sha256 (بدل hash() المتقلب).
- يقبل إما:
    * analysis+lang  --> يُولّد المفتاح ذاتيًا من JSON مفرز
    * key="..."      --> يستخدم المفتاح كما هو
    * analysis كـ str جاهز (مفتاح) --> يُستخدم كما هو (توافقًا مع استدعاءات قديمة)
- build_persona_cache_key(...) لتكوين مفتاح ثابت موحّد من أجزاء مختارة (lang، z_scores، prefs…).

واجهات عامة:
- get_cached_personality(analysis=None, lang="العربية", key=None) -> Optional[str]
- save_cached_personality(analysis=None, personality="", lang="العربية", key=None) -> str
- build_persona_cache_key(...)
- get_cache_stats() -> Dict[str, Any]
- clear_cache() -> None
"""

from __future__ import annotations
import json, time, hashlib
from typing import Any, Dict, Optional

# في الذاكرة
_PERSONA_CACHE: Dict[str, str] = {}

# إحصائيات
_STATS = {
    "hits": 0,
    "misses": 0,
    "last_key": None,
    "last_action": None,     # "HIT" | "MISS" | "SET" | "CLEAR"
    "last_set_ts": None,     # unix ts
    "last_get_ts": None,     # unix ts
    "last_get_ms": None,     # زمن آخر get (ms)
    "size": 0,
}

# ---------------------------
# مفاتيح الكاش: توليد ثابت
# ---------------------------
def _stable_digest(obj: Any) -> str:
    """SHA256 لتمثيل JSON ثابت (مع sort_keys)."""
    try:
        payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        payload = str(obj)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _key_for(analysis: Any, lang: str) -> str:
    """
    يبني مفتاحًا حتميًا من analysis+lang.
    - لو analysis سترنق طويل وفيه ':' نعتبره مفتاحًا جاهزًا (توافقًا).
    - وإلا نُولّد sha256 من الـ analysis (JSON مفرز) مضافًا له lang.
    """
    if isinstance(analysis, str) and (":" in analysis and len(analysis) >= 12):
        # اعتبره precomputed key (توافقًا مع استدعاءات مرّت سترنق كمفتاح)
        return analysis

    # لو التحليل يحتوي encoded_profile حاول نختصر على عناصر مؤثرة
    base: Dict[str, Any] = {"lang": lang}
    try:
        if isinstance(analysis, dict):
            enc = analysis.get("encoded_profile") or {}
            # اشمل درجات Z (الأكثر تأثيرًا لاستقرار الشخصية)
            zs = enc.get("scores") or enc.get("z_scores") or {}
            prefs = enc.get("prefs") or enc.get("preferences") or {}
            qp = analysis.get("quick_profile", None)
            # لو ما فيه encoded_profile، استخدم silent_drivers كبديل خفيف
            sdrivers = analysis.get("silent_drivers", None)

            base.update({
                "z_scores": zs,
                "prefs": prefs,
                "quick_profile": qp,
                "silent_drivers": sdrivers
            })
        else:
            base["analysis"] = analysis
    except Exception:
        base["analysis"] = analysis

    digest = _stable_digest(base)
    return f"{lang}:{digest[:24]}"

# ---------------------------
# واجهات الكاش
# ---------------------------
def get_cached_personality(analysis: Dict[str, Any] = None,
                           lang: str = "العربية",
                           key: str = None) -> Optional[str]:
    """
    جلب شخصية من الكاش.
    - analysis+lang: يُشتق المفتاح تلقائيًا.
    - key: يستخدم كما هو.
    - تمرير analysis كـ str (وفيه ':') يُعتبر مفتاحًا جاهزًا (توافق).
    """
    start = time.perf_counter()

    if key is not None:
        k = key
    elif isinstance(analysis, str) and (":" in analysis and len(analysis) >= 12):
        k = analysis  # مفتاح جاهز مُمرّر بالخطأ في وسيط analysis
    else:
        k = _key_for(analysis or {}, lang)

    persona = _PERSONA_CACHE.get(k)

    took_ms = int((time.perf_counter() - start) * 1000)
    _STATS["last_get_ts"] = time.time()
    _STATS["last_get_ms"] = took_ms
    _STATS["last_key"] = k

    if persona is None:
        _STATS["misses"] += 1
        _STATS["last_action"] = "MISS"
    else:
        _STATS["hits"] += 1
        _STATS["last_action"] = "HIT"

    return persona

def save_cached_personality(analysis: Dict[str, Any] = None,
                            personality: str = "",
                            lang: str = "العربية",
                            key: str = None) -> str:
    """
    حفظ شخصية في الكاش وإرجاع المفتاح المستخدم.
    - لو مرّرت key نستخدمه مباشرة.
    - غير ذلك ننشئ مفتاحًا ثابتًا من analysis+lang.
    """
    if key is not None:
        k = key
    elif isinstance(analysis, str) and (":" in analysis and len(analysis) >= 12):
        k = analysis  # اعتبره مفتاحًا جاهزًا
    else:
        k = _key_for(analysis or {}, lang)

    _PERSONA_CACHE[k] = personality or ""
    _STATS["size"] = len(_PERSONA_CACHE)
    _STATS["last_key"] = k
    _STATS["last_action"] = "SET"
    _STATS["last_set_ts"] = time.time()
    return k

# ---------------------------
# دوال مساعدة
# ---------------------------
def build_persona_cache_key(lang: str,
                            answers_min: Dict[str, Any] | None = None,
                            z_scores: Dict[str, Any] | None = None,
                            prefs: Dict[str, Any] | None = None,
                            quick_profile: str | None = None,
                            silent_drivers: Any = None) -> str:
    """
    يبني مفتاح كاش ثابت من العناصر الأكثر تأثيرًا.
    استخدمه في الأماكن اللي تبغى فيها مفتاحًا موحّدًا بصراحة.
    """
    base = {
        "lang": lang,
        "z_scores": z_scores or {},
        "prefs": prefs or {},
        "quick_profile": quick_profile,
        "silent_drivers": silent_drivers,
        # answers_min اختياري: مرّر نسخة مختزلة (مو ضروري)
        "answers_hint": answers_min or {},
    }
    return f"{lang}:{_stable_digest(base)[:24]}"

def get_cache_stats() -> Dict[str, Any]:
    """إرجاع عدادات الكاش للعرض في الواجهة أو اللوج."""
    return dict(_STATS)

def clear_cache() -> None:
    _PERSONA_CACHE.clear()
    _STATS.update({
        "hits": 0, "misses": 0, "last_key": None, "last_action": "CLEAR",
        "last_set_ts": None, "last_get_ts": None, "last_get_ms": None,
        "size": 0
    })
