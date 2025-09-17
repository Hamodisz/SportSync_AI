# -- coding: utf-8 --
"""
core/recs/config_runtime.py
---------------------------
تفكيك إعدادات التشغيل من core/backend_gpt.py:
- قراءة مفاتيح البيئة وتهيئة عميل OpenAI (أو بدائل base_url/organization)
- تحميل إعدادات التطبيق CFG عبر core.app_config.get_config()
- ثوابت التشغيل (نموذج الدردشة، حراس الجودة، ميزانية الوقت...)
- دوال تشخيصية بسيطة (_dbg)

يُستورد هذا الملف من بقية الوحدات:
    from core.recs.config_runtime import (
        CFG, CHAT_MODEL, ALLOW_SPORT_NAMES,
        REC_RULES, _MIN_CHARS, _REQUIRE_WIN, _MIN_CORE_SKILLS,
        REC_BUDGET_S, REC_REPAIR_ENABLED, REC_FAST_MODE, REC_DEBUG,
        CHAT_MODEL_FALLBACK, MAX_PROMPT_CHARS, EGCFG, OpenAI_CLIENT, _dbg
    )
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

# ========= OpenAI =========
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("أضف الحزمة في requirements: openai>=1.6.1,<2") from e

# نقرأ المفتاح من أكثر من احتمال (OpenAI / OpenRouter / Azure)
OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENROUTER_API_KEY")
    or os.getenv("AZURE_OPENAI_API_KEY")
)

# عنوان الـ Base URL (اختياري مع OpenRouter/Azure)
OPENAI_BASE_URL = (
    os.getenv("OPENAI_BASE_URL")
    or os.getenv("OPENROUTER_BASE_URL")
    or os.getenv("AZURE_OPENAI_ENDPOINT")
)

OPENAI_ORG = os.getenv("OPENAI_ORG")  # غالباً فاضي

OpenAI_CLIENT = None
if OPENAI_API_KEY:
    try:
        kwargs: Dict[str, Any] = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL
        if OPENAI_ORG:
            kwargs["organization"] = OPENAI_ORG
        OpenAI_CLIENT = OpenAI(**kwargs)
    except Exception as e:
        print(f"[ENV] ⚠️ فشل إنشاء عميل OpenAI: {e}")
        OpenAI_CLIENT = None
else:
    print("[ENV] ⚠️ لا يوجد API key في المتغيرات البيئية.")

# طباعة حالة الإقلاع للتشخيص (مرة واحدة عند الاستيراد)
print(
    f"[BOOT] LLM READY? {'YES' if OpenAI_CLIENT else 'NO'} | "
    f"base={OPENAI_BASE_URL or 'default'} | "
    f"model={os.getenv('CHAT_MODEL','gpt-4o-mini')}"
)

# ========= App Config =========
try:
    from core.app_config import get_config
    CFG: Dict[str, Any] = get_config()
except Exception:
    CFG = {}

CHAT_MODEL: str = (CFG.get("llm") or {}).get("model", os.getenv("CHAT_MODEL", "gpt-4o"))
ALLOW_SPORT_NAMES: bool = (CFG.get("recommendations") or {}).get("allow_sport_names", True)

REC_RULES: Dict[str, Any] = (CFG.get("recommendations") or {})
_MIN_CHARS: int = int(REC_RULES.get("min_chars", 220))
_REQUIRE_WIN: bool = bool(REC_RULES.get("require_win_condition", True))
_MIN_CORE_SKILLS: int = int(REC_RULES.get("min_core_skills", 3))

# ========= Runtime Guards / Tunables =========
REC_BUDGET_S: float = float(os.getenv("REC_BUDGET_S", "22"))
REC_REPAIR_ENABLED: bool = os.getenv("REC_REPAIR_ENABLED", "1") == "1"
REC_FAST_MODE: bool = os.getenv("REC_FAST_MODE", "0") == "1"
REC_DEBUG: bool = os.getenv("REC_DEBUG", "0") == "1"
CHAT_MODEL_FALLBACK: str = os.getenv("CHAT_MODEL_FALLBACK", "gpt-4o-mini")
MAX_PROMPT_CHARS: int = int(os.getenv("MAX_PROMPT_CHARS", "6000"))

def _dbg(msg: str) -> None:
    """طباعة رسائل تشخيصية فقط إذا REC_DEBUG=1."""
    if REC_DEBUG:
        print(f"[RECDBG] {msg}")

# Evidence Gate thresholds (defaults if not provided)
if isinstance(CFG.get("analysis"), dict):
    EGCFG: Dict[str, Any] = (CFG.get("analysis") or {}).get("egate", {}) or {}
else:
    EGCFG = {}

# ملاحظات:
# - هذا الملف لا يعتمد على بقية الوحدات (لا circular imports).
# - أي وحدة تحتاج إعدادات/عميل LLM أو ثوابت تشغيل، تستورد من هنا.
