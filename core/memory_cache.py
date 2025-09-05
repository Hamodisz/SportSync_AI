# -- coding: utf-8 --
"""
core/memory_cache.py
--------------------
كاش سريع بالذاكرة لشخصية المدرب (persona) + توصيات الهوية (cards).

المزايا:
- مفاتيح ثابتة عبر SHA256 لتمثيل JSON مفرز (بدون اعتماد على hash() المتقلب).
- كاش persona: get_cached_personality / save_cached_personality (كما هو مع تحسينات طفيفة).
- كاش التوصيات: get_cached_recommendation / save_cached_recommendation
  * مفتاح موحّد: يعتمد على lang + user_id + fingerprint(answers)
  * لا نخزن الإجابات نفسها، فقط البصمة.
  * إخلاء (eviction) بسيط أقدمية عند تجاوز حد الحجم.
- إحصائيات منفصلة لكل نوع.

واجهات عامة:
- Persona:
    get_cached_personality(analysis=None, lang="العربية", key=None) -> Optional[str]
    save_cached_personality(analysis=None, personality="", lang="العربية", key=None) -> str
    build_persona_cache_key(...)
- Recommendations:
    get_cached_recommendation(user_id: str, answers: dict, lang: str, max_age_s: int | None = None) -> Optional[list[str]]
    save_cached_recommendation(user_id: str, answers: dict, lang: str, cards: list[str]) -> str
- إدارة:
    get_cache_stats() -> Dict[str, Any]
    clear_cache() -> None
    clear_recs_cache() -> None
"""

from __future__ import annotations
import json, time, hashlib
from typing import Any, Dict, Optional, List

# =========================
# أدوات مساعدة (ثابتة)
# =========================
def _stable_digest(obj: Any) -> str:
    """SHA256 لتمثيل JSON ثابت (sort_keys=True)."""
    try:
        payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        payload = str(obj)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _short_sha(s: str, n: int = 10) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:max(4, n)]

# =========================
# كاش الـ Persona
# =========================
_PERSONA_CACHE: Dict[str, str] = {}

# إحصائيات عامة + مفصلة
_STATS: Dict[str, Any] = {
    # persona
    "persona_hits": 0,
    "persona_misses": 0,
    "persona_last_key": None,
    "persona_last_action": None,  # "HIT"|"MISS"|"SET"|"CLEAR"
    "persona_last_set_ts": None,
    "persona_last_get_ts": None,
    "persona_last_get_ms": None,
    "persona_size": 0,
    # recs
    "recs_hits": 0,
    "recs_misses": 0,
    "recs_last_key": None,
    "recs_last_action": None,
    "recs_last_set_ts": None,
    "recs_last_get_ts": None,
    "recs_last_get_ms": None,
    "recs_size": 0,
}

# حدود الكاش للتوصيات (يمكن تعديلها حسب الحاجة)
_RECS_MAX_ENTRIES = 1024  # حد أقصى لعدد المفاتيح قبل الإخلاء
_RECS_CACHE: Dict[str, Dict[str, Any]] = {}  # key -> {"cards": List[str], "ts": float}

# ---------------------------
# مفاتيح الكاش: Persona
# ---------------------------
def _persona_key_for(analysis: Any, lang: str) -> str:
    """
    يبني مفتاحًا حتميًا من analysis+lang.
    - لو analysis سترنق طويلة وبها ':' نعتبره مفتاحًا جاهزًا (توافقًا).
    """
    if isinstance(analysis, str) and (":" in analysis and len(analysis) >= 12):
        return analysis  # precomputed key
    base: Dict[str, Any] = {"lang": lang}
    try:
        if isinstance(analysis, dict):
            enc = analysis.get("encoded_profile") or {}
            zs = enc.get("scores") or enc.get("z_scores") or {}
            prefs = enc.get("prefs") or enc.get("preferences") or {}
            qp = analysis.get("quick_profile", None)
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
        k = analysis
    else:
        k = _persona_key_for(analysis or {}, lang)

    persona = _PERSONA_CACHE.get(k)

    took_ms = int((time.perf_counter() - start) * 1000)
    _STATS["persona_last_get_ts"] = time.time()
    _STATS["persona_last_get_ms"] = took_ms
    _STATS["persona_last_key"] = k

    if persona is None:
        _STATS["persona_misses"] += 1
        _STATS["persona_last_action"] = "MISS"
    else:
        _STATS["persona_hits"] += 1
        _STATS["persona_last_action"] = "HIT"

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
        k = analysis
    else:
        k = _persona_key_for(analysis or {}, lang)

    _PERSONA_CACHE[k] = personality or ""
    _STATS["persona_size"] = len(_PERSONA_CACHE)
    _STATS["persona_last_key"] = k
    _STATS["persona_last_action"] = "SET"
    _STATS["persona_last_set_ts"] = time.time()
    return k

def build_persona_cache_key(lang: str,
                            answers_min: Dict[str, Any] | None = None,
                            z_scores: Dict[str, Any] | None = None,
                            prefs: Dict[str, Any] | None = None,
                            quick_profile: str | None = None,
                            silent_drivers: Any = None) -> str:
    """مفتاح موحّد ثابت لعناصر مؤثرة في الشخصية."""
    base = {
        "lang": lang,
        "z_scores": z_scores or {},
        "prefs": prefs or {},
        "quick_profile": quick_profile,
        "silent_drivers": silent_drivers,
        "answers_hint": answers_min or {},
    }
    return f"{lang}:{_stable_digest(base)[:24]}"

# ---------------------------
# مفاتيح الكاش: Recommendations
# ---------------------------
def _answers_fingerprint(answers: Dict[str, Any]) -> str:
    """بصمة ثابتة للإجابات (JSON مفرز)."""
    try:
        return _stable_digest(answers)[:24]
    except Exception:
        return _short_sha(str(answers), 24)

def _recs_key_for(user_id: str, answers: Dict[str, Any], lang: str) -> str:
    uid_short = _short_sha(user_id or "anon", 10)
    fp = _answers_fingerprint(answers or {})
    return f"recs:{lang}:{uid_short}:{fp}"

def _recs_enforce_limit() -> None:
    """إخلاء أقدم عنصر إذا تجاوزنا الحد."""
    global _RECS_CACHE
    if len(_RECS_CACHE) <= _RECS_MAX_ENTRIES:
        return
    # احذف الأقدم (أصغر timestamp)
    oldest_key = None
    oldest_ts = float("inf")
    for k, v in _RECS_CACHE.items():
        ts = float(v.get("ts", 0.0) or 0.0)
        if ts < oldest_ts:
            oldest_ts = ts
            oldest_key = k
    if oldest_key:
        _RECS_CACHE.pop(oldest_key, None)

def get_cached_recommendation(user_id: str,
                              answers: Dict[str, Any],
                              lang: str,
                              max_age_s: Optional[int] = None) -> Optional[List[str]]:
    """
    يعيد الكروت (3 نصوص) إن وُجدت بنفس user_id+answers+lang.
    - max_age_s اختياري لرفض النتائج القديمة (TTL بالقراءة فقط).
    """
    start = time.perf_counter()
    k = _recs_key_for(user_id, answers, lang)
    rec = _RECS_CACHE.get(k)

    took_ms = int((time.perf_counter() - start) * 1000)
    _STATS["recs_last_get_ts"] = time.time()
    _STATS["recs_last_get_ms"] = took_ms
    _STATS["recs_last_key"] = k

    if not rec:
        _STATS["recs_misses"] += 1
        _STATS["recs_last_action"] = "MISS"
        return None

    if max_age_s is not None:
        ts = float(rec.get("ts", 0.0) or 0.0)
        if (time.time() - ts) > max_age_s:
            # منتهٍ: احذفه واعتبرها MISS
            _RECS_CACHE.pop(k, None)
            _STATS["recs_size"] = len(_RECS_CACHE)
            _STATS["recs_misses"] += 1
            _STATS["recs_last_action"] = "MISS"
            return None

    _STATS["recs_hits"] += 1
    _STATS["recs_last_action"] = "HIT"
    return list(rec.get("cards") or [])

def save_cached_recommendation(user_id: str,
                               answers: Dict[str, Any],
                               lang: str,
                               cards: List[str]) -> str:
    """
    يحفظ الكروت في الكاش، ويعيد المفتاح المستخدم.
    """
    k = _recs_key_for(user_id, answers, lang)
    _RECS_CACHE[k] = {"cards": list(cards or []), "ts": time.time()}
    _recs_enforce_limit()
    _STATS["recs_size"] = len(_RECS_CACHE)
    _STATS["recs_last_key"] = k
    _STATS["recs_last_action"] = "SET"
    _STATS["recs_last_set_ts"] = time.time()
    return k

# ---------------------------
# إدارة عامة
# ---------------------------
def get_cache_stats() -> Dict[str, Any]:
    """إرجاع عدادات الكاش (persona + recs)."""
    return dict(_STATS)

def clear_recs_cache() -> None:
    _RECS_CACHE.clear()
    _STATS.update({
        "recs_hits": 0, "recs_misses": 0, "recs_last_key": None, "recs_last_action": "CLEAR",
        "recs_last_set_ts": None, "recs_last_get_ts": None, "recs_last_get_ms": None,
        "recs_size": 0
    })

def clear_cache() -> None:
    _PERSONA_CACHE.clear()
    clear_recs_cache()
    _STATS.update({
        "persona_hits": 0, "persona_misses": 0, "persona_last_key": None, "persona_last_action": "CLEAR",
        "persona_last_set_ts": None, "persona_last_get_ts": None, "persona_last_get_ms": None,
        "persona_size": 0
    })
