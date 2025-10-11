# -- coding: utf-8 --
"""
core/user_logger.py
-------------------
تسجيل بسيط لأحداث المستخدمين في JSONL (سطر لكل حدث) داخل data/logs/.
- خفيف، بدون تبعيات.
- آمن ضد الأعطال (try/except).
- يشتغل حتى لو ما فيه DataPipe.
"""

from __future__ import annotations
import os, json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# مسار ملفات اللوج
ROOT = Path(__file__).resolve().parent.parent  # إلى جذر المشروع
LOG_DIR = (ROOT / "data" / "logs").resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "events.jsonl"

# محاولة ربط DataPipe (اختياري)
try:
    from core.data_pipe import get_pipe
    _PIPE = get_pipe()
except Exception:
    _PIPE = None

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _safe(obj: Any) -> Any:
    try:
        json.dumps(obj, ensure_ascii=False)
        return obj
    except Exception:
        # آخر حل: تحويل إلى string
        return str(obj)

def _append_jsonl(row: Dict[str, Any]) -> None:
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        # كحل أخير: اطبع للكونسول
        print("[USER_LOGGER][WARN] failed to write log row")

def log_user_insight(
    user_id: str,
    content: Dict[str, Any],
    event_type: str = "generic",
    app_version: Optional[str] = None,
    model: Optional[str] = None,
    lang: Optional[str] = None
) -> None:
    """تسجيل حدث عام."""
    row = {
        "ts": _now_iso(),
        "event": event_type,
        "user_id": user_id or "anon",
        "lang": lang,
        "model": model,
        "app_ver": app_version,
        "content": _safe(content),
    }
    _append_jsonl(row)

    # إرسال اختياري لقناة خارجية (لو مفعّل DataPipe)
    if _PIPE:
        try:
            _PIPE.send(event_type=event_type, payload=row, user_id=user_id, lang=lang, model=model)
        except Exception:
            pass

# ــــــــــــــــــــــ دوال مساعدة سريعة ــــــــــــــــــــــ

def log_recommendation_result(
    user_id: str,
    answers: Dict[str, Any],
    recs_text: list[str],
    timings: Optional[Dict[str, float]] = None,
    lang: str = "العربية",
    model: Optional[str] = None,
    app_version: Optional[str] = None
) -> None:
    """تسجيل نتيجة توصيات (النصوص + تايمرز إن وُجدت)."""
    content = {
        "answers": _safe(answers),
        "recommendations": [str(x) for x in (recs_text or [])],
        "timings": timings or {},
    }
    log_user_insight(
        user_id=user_id,
        content=content,
        event_type="recommendation_result",
        app_version=app_version,
        model=model,
        lang=lang
    )

def log_rating(
    user_id: str,
    ratings: list[int],
    rec_ids: Optional[list[str]] = None,
    lang: str = "العربية",
    app_version: Optional[str] = None
) -> None:
    """تسجيل تقييمات المستخدم للتوصيات."""
    content = {
        "ratings": [int(x) for x in (ratings or [])],
        "rec_ids": rec_ids or []
    }
    log_user_insight(
        user_id=user_id,
        content=content,
        event_type="rating",
        app_version=app_version,
        lang=lang
    )

def log_chat_message(
    user_id: str,
    user_message: str,
    ai_reply: str,
    lang: str = "العربية",
    model: Optional[str] = None,
    app_version: Optional[str] = None,
    streaming: bool = False
) -> None:
    """تسجيل تفاعل محادثة (رسالة المستخدم + رد الذكاء الاصطناعي)."""
    content = {
        "user_message": str(user_message or ""),
        "ai_reply": str(ai_reply or ""),
        "streaming": bool(streaming)
    }
    log_user_insight(
        user_id=user_id,
        content=content,
        event_type="chat_interaction",
        app_version=app_version,
        model=model,
        lang=lang
    )
