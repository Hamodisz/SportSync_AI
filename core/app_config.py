# -- coding: utf-8 --
"""
core/app_config.py
------------------
Loader لإعدادات التطبيق من ملف محلي + اختيارياً من رابط خارجي.
- يقرأ: data/app_config.json (إن وُجد)
- يدمج مع نسخة remote JSON (إن تم ضبط remote.config_url)
- يدعم cache مع TTL تلقائي
- ENV تظل أعلى أولوية لو حاب تتجاوز (مثال CHAT_MODEL)
"""

from __future__ import annotations
import os, json, time, threading
from typing import Any, Dict

_CFG_PATH = os.getenv("APPCONFIG_PATH", "data/app_config.json")
_TTL_SECS = 60           # إعادة قراءة الملف المحلي كل ~دقيقة
_REMOTE_TTL_SECS = 900   # إعادة جلب النسخة البعيدة كل ~15 دقيقة
_LOCK = threading.RLock()

_cache: Dict[str, Any] = {}
_last_read_local = 0.0
_last_read_remote = 0.0

def _read_local() -> Dict[str, Any]:
    try:
        with open(_CFG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _fetch_remote(url: str, timeout: int = 8) -> Dict[str, Any]:
    try:
        import requests
        r = requests.get(url, timeout=timeout)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {}

def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def _env_overrides(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # Overrides من ENV لو حاب تغيّر سريعًا بدون تعديل الملف
    if os.getenv("CHAT_MODEL"):
        cfg.setdefault("llm", {})["model"] = os.getenv("CHAT_MODEL")
    if os.getenv("ALLOW_SPORT_NAMES"):
        val = os.getenv("ALLOW_SPORT_NAMES", "true").lower() in ("1","true","yes","y")
        cfg.setdefault("recommendations", {})["allow_sport_names"] = val
    if os.getenv("APP_VERSION"):
        cfg["app_version"] = os.getenv("APP_VERSION")
    return cfg

def get_config() -> Dict[str, Any]:
    global _cache, _last_read_local, _last_read_remote
    now = time.time()
    with _LOCK:
        need_local = (now - _last_read_local) > _TTL_SECS or not _cache
        if need_local:
            local_cfg = _read_local()
            _cache = local_cfg
            _last_read_local = now

        # remote merge (لو مضبوط)
        remote = (_cache.get("remote") or {})
        url = remote.get("config_url")
        refresh = int(remote.get("refresh_secs", _REMOTE_TTL_SECS))
        if url and ((now - _last_read_remote) > max(30, refresh)):
            remote_cfg = _fetch_remote(url)
            if remote_cfg:
                _cache = _deep_merge(_cache, remote_cfg)
            _last_read_remote = now

        _cache = _env_overrides(_cache)

        # Defaults
        _cache.setdefault("app_version", "dev")
        _cache.setdefault("llm", {}).setdefault("model", "gpt-4o")
        _cache.setdefault("recommendations", {}).setdefault("allow_sport_names", True)
        _cache["sinks"] = _cache.get("sinks") or {
            "disk": {"enabled": True, "path": "./data/events.jsonl"},
            "webhook": {"enabled": False, "url": ""},
            "gsheets": {"enabled": False, "sheet_id": "", "service_account_json": ""}
        }
        return _cache
