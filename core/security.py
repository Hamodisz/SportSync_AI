# -- coding: utf-8 --
# core/security.py
from _future_ import annotations
from urllib.parse import urlparse
import re
from typing import Dict

_URL_RE = re.compile(r'(https?://[^\s\]\)<>"]+)', re.IGNORECASE)

def _host(url: str) -> str:
    try:
        u = urlparse(url)
        return (u.netloc or "").split("@")[-1].split(":")[0].lower()
    except Exception:
        return ""

def is_allowed_url(url: str, cfg: Dict) -> bool:
    try:
        u = urlparse(url)
        if not u.scheme or not u.netloc:
            return False
        sec = (cfg or {}).get("security", {}) if isinstance(cfg, dict) else {}
        require_https = bool(sec.get("require_https", True))
        if require_https and u.scheme.lower() != "https":
            return False
        host = _host(url)
        allowed = set(x.lower() for x in (sec.get("allowed_domains") or []))
        blocked = set(x.lower() for x in (sec.get("blocked_domains") or []))
        if host in blocked:
            return False
        if allowed:
            return host in allowed
        return True
    except Exception:
        return False

def scrub_unknown_urls(text: str, cfg: Dict) -> str:
    """يُبقي الروابط المسموح بها كما هي، ويُعمّي البقية (hxxp + [.] بدل .)."""
    if not text:
        return text
    def repl(m):
        url = m.group(1)
        return url if is_allowed_url(url, cfg) else url.replace("http", "hxxp").replace(".", "[.]")
    return _URL_RE.sub(repl, text)
