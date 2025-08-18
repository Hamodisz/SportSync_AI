# -- coding: utf-8 --
"""
core/memory_cache.py
كاش بسيط لشخصية المدرب (persona) مع عدادات HIT/MISS وقياسات زمنية.
مفتاح الكاش = (lang, hash(analysis_json_sorted))
"""

from __future__ import annotations
import json, time
from typing import Any, Dict, Optional, Tuple

# ذاكرة الكاش
_PERSONA_CACHE: Dict[str, str] = {}
# إحصائيات
_STATS = {
    "hits": 0,
    "misses": 0,
    "last_key": None,
    "last_action": None,     # "HIT" or "MISS" or "SET"
    "last_set_ts": None,     # timestamp
    "last_get_ts": None,     # timestamp
    "last_get_ms": None,     # زمن آخر get (ms)
    "size": 0,
}

def _key_for(analysis: Dict[str, Any], lang: str) -> str:
    # نبني مفتاحًا حتميًا (stable) من JSON مفرز
    try:
        payload = json.dumps(analysis, ensure_ascii=False, sort_keys=True)
    except Exception:
        payload = str(analysis)
    return f"{lang}:{hash(payload)}"

def get_cached_personality(analysis: Dict[str, Any] = None, lang: str = "العربية", key: str = None) -> Optional[str]:
    """
    جلب شخصية من الكاش.
    - إما تعطي analysis+lang (المعتاد)
    - أو تعطي key جاهز (حالة ديناميكية)
    """
    start = time.perf_counter()
    if key is None:
        key = _key_for(analysis or {}, lang)
    persona = _PERSONA_CACHE.get(key)
    took_ms = int((time.perf_counter() - start) * 1000)

    _STATS["last_get_ts"] = time.time()
    _STATS["last_get_ms"] = took_ms
    _STATS["last_key"] = key
    if persona is None:
        _STATS["misses"] += 1
        _STATS["last_action"] = "MISS"
    else:
        _STATS["hits"] += 1
        _STATS["last_action"] = "HIT"
    return persona

def save_cached_personality(analysis: Dict[str, Any] = None, personality: str = "", lang: str = "العربية", key: str = None) -> str:
    """
    حفظ شخصية في الكاش وإرجاع المفتاح المستخدم.
    """
    if key is None:
        key = _key_for(analysis or {}, lang)
    _PERSONA_CACHE[key] = personality or ""
    _STATS["size"] = len(_PERSONA_CACHE)
    _STATS["last_key"] = key
    _STATS["last_action"] = "SET"
    _STATS["last_set_ts"] = time.time()
    return key

def get_cache_stats() -> Dict[str, Any]:
    """إرجاع عدادات الكاش للعرض في الواجهة أو اللوج."""
    return dict(_STATS)

def clear_cache() -> None:
    _PERSONA_CACHE.clear()
    for k in list(_STATS.keys()):
        if isinstance(_STATS[k], int):
            _STATS[k] = 0
        else:
            _STATS[k] = None
    _STATS["size"] = 0
