# -- coding: utf-8 --
"""
core/security.py
----------------
تنظيف الروابط داخل نص/كرت قبل عرضه للمستخدم.
- يعتمد على إعدادات security داخل data/app_config.json
- سياسة صارمة: منع افتراضيًا إذا لم توجد allowed_domains
- يحترم فلاغ scrub_urls (للتعطيل المؤقت)

مثال إعدادات:
"security": {
  "scrub_urls": true,
  "require_https": true,
  "allowed_domains": ["sportsync.ai", "yourdomain.com"],
  "blocked_domains": []
}
"""

from _future_ import annotations
import re
from urllib.parse import urlparse, ParseResult
from typing import Any, Dict

# نلتقط الروابط القياسية http/https (بدون أقواس وزوايا)
_URL_RE = re.compile(r'(https?://[^\s\]\)\<\>"]+)', re.IGNORECASE)


def _host(url: str) -> str:
    """إرجاع النطاق دون منفذ/اعتماديات."""
    try:
        u = urlparse(url)
        # نتخلّص من user:pass@host:port
        netloc = (u.netloc or "").split("@")[-1].split(":")[0]
        return netloc.lower()
    except Exception:
        return ""


def _obfuscate(u: ParseResult) -> str:
    """حوّل الرابط لصيغة غير قابلة للنقر (hxxp + [.] في الدومين)."""
    scheme = "hxxps" if (u.scheme or "").lower().startswith("https") else "hxxp"
    host = (u.netloc or "").split("@")[-1]
    host = host.replace(".", "[.]")
    path = u.path or ""
    q = ("?" + u.query) if u.query else ""
    f = ("#" + u.fragment) if u.fragment else ""
    return f"{scheme}://{host}{path}{q}{f}"


def is_allowed_url(url: str, cfg: Dict) -> bool:
    """
    قرار السماح/المنع:
      - إن scrub_urls=false → اسمح بكل شيء (تعطيل مؤقت).
      - إن require_https=true → امنع غير HTTPS.
      - إن host ضمن blocked_domains → امنع.
      - إن allowed_domains غير فارغة → اسمح فقط لما بداخلها.
      - إن allowed_domains فارغة → امنع افتراضيًا (صارم).
    """
    try:
        u = urlparse(url)
        if not u.scheme or not u.netloc:
            return False

        sec = (cfg or {}).get("security") or {}

        # تعطيل التنظيف كليًا (ميزة مؤقتة)
        if not bool(sec.get("scrub_urls", True)):
            return True

        require_https = bool(sec.get("require_https", True))
        if require_https and u.scheme.lower() != "https":
            return False

        host = _host(url)
        allowed = {x.lower() for x in (sec.get("allowed_domains") or [])}
        blocked = {x.lower() for x in (sec.get("blocked_domains") or [])}

        if host in blocked:
            return False

        if allowed:
            return host in allowed

        # لا توجد قائمة سماح → منع افتراضيًا
        return False
    except Exception:
        return False


def _scrub_text(text: str, cfg: Dict) -> str:
    """نظّف الروابط داخل نص واحد."""
    if not text:
        return text

    def repl(m: re.Match) -> str:
        url = m.group(1)
        try:
            if is_allowed_url(url, cfg):
                return url  # يُسمح به كما هو
            # خلاف ذلك → إخفاء
            return _obfuscate(urlparse(url))
        except Exception:
            return url

    return _URL_RE.sub(repl, text)


def scrub_unknown_urls(obj: Any, cfg: Dict) -> Any:
    """
    ينظّف الروابط داخل:
      - str: يرجع نصًا منظّفًا
      - list/tuple: ينظّف عناصرها
      - dict: ينظّف القيم (لا يلمس المفاتيح)
    يُعيد نفس النوع.
    """
    # نص
    if isinstance(obj, str):
        return _scrub_text(obj, cfg)

    # قائمة/تربل
    if isinstance(obj, (list, tuple)):
        cleaned = [scrub_unknown_urls(x, cfg) for x in obj]
        return type(obj)(cleaned)

    # قاموس
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out[k] = scrub_unknown_urls(v, cfg)
        return out

    # أنواع أخرى نعيدها كما هي
    return obj
