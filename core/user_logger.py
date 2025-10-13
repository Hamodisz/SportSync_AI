# -- coding: utf-8 --
"""
core/user_logger.py
-------------------
تسجيل بسيط لأحداث المستخدمين في JSONL (سطر لكل حدث) داخل data/logs/.
- خفيف ومرن مع الوسائط (يقبل **kwargs).
- متوافق مع الدوال القديمة: log_recommendation_result / log_rating / log_chat_message
- يضيف الدوال التي يستخدمها app.py: log_quiz_submission / log_event
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
    from core.data_pipe import get_pipe  # إن وُجد
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
        return str(obj)

def _append_jsonl(row: Dict[str, Any]) -> None:
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        print("[USER_LOGGER][WARN] failed to write log row")

def _emit_pipe(event_type: str, payload: Dict[str, Any], user_id: str, lang: Optional[str], model: Optional[str]) -> None:
    if not _PIPE:
        return
    try:
        _PIPE.send(event_type=event_type, payload=payload, user_id=user_id, lang=lang, model=model)
    except Exception:
        pass

def log_user_insight(
    user_id: str,
    content: Dict[str, Any],
    event_type: str = "generic",
    *,
    session_id: Optional[str] = None,
    app_version: Optional[str] = None,
    model: Optional[str] = None,
    lang: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """الأساس: يكتب سطر JSONL واحد."""
    row = {
        "ts": _now_iso(),
        "event": event_type,
        "user_id": user_id or "anon",
        "session_id": session_id,
        "lang": lang,
        "model": model,
        "app_ver": app_version,
        "content": _safe(content),
        "meta": _safe(meta or {}),
    }
    _append_jsonl(row)
    _emit_pipe(event_type, row, user_id, lang, model)

# --------- دوال يستخدمها app.py ---------

def log_quiz_submission(
    *,
    user_id: str,
    answers: Dict[str, Any],
    lang: str,
    session_id: Optional[str],
    meta: Optional[Dict[str, Any]] = None,
    app_version: Optional[str] = None,
    model: Optional[str] = None,
    **_
) -> None:
    """تسجيل إرسال الإجابات من واجهة الكويز."""
    content = {"answers": _safe(answers)}
    log_user_insight(
        user_id=user_id,
        content=content,
        event_type="quiz_submission",
        session_id=session_id,
        app_version=app_version,
        model=model,
        lang=lang,
        meta=meta,
    )

def log_event(
    *,
    user_id: str,
    session_id: Optional[str],
    name: str,
    payload: Optional[Dict[str, Any]] = None,
    lang: Optional[str] = None,
    app_version: Optional[str] = None,
    model: Optional[str] = None,
    **_
) -> None:
    """تسجيل أي حدث عام (فتح/إغلاق محادثة… إلخ)."""
    content = {"name": name, "payload": _safe(payload or {})}
    log_user_insight(
        user_id=user_id,
        content=content,
        event_type="event",
        session_id=session_id,
        app_version=app_version,
        model=model,
        lang=lang,
    )

# --------- توافُق مع الدوال القديمة + المستخدمة في backend_gpt ---------

def log_recommendation_result(
    user_id: str,
    answers: Dict[str, Any],
    recs_text: list[str],
    timings: Optional[Dict[str, float]] = None,
    lang: str = "العربية",
    model: Optional[str] = None,
    app_version: Optional[str] = None,
    session_id: Optional[str] = None,
    **_
) -> None:
    content = {
        "answers": _safe(answers),
        "recommendations": [str(x) for x in (recs_text or [])],
        "timings": timings or {},
    }
    log_user_insight(
        user_id=user_id,
        content=content,
        event_type="recommendation_result",
        session_id=session_id,
        app_version=app_version,
        model=model,
        lang=lang,
    )

def log_rating(
    user_id: str,
    rating: int,
    *,
    session_id: Optional[str] = None,
    index: Optional[int] = None,
    rec_ids: Optional[list[str]] = None,
    lang: str = "العربية",
    app_version: Optional[str] = None,
    model: Optional[str] = None,
    **_
) -> None:
    content = {
        "rating": int(rating),
        "index": index,
        "rec_ids": rec_ids or [],
    }
    log_user_insight(
        user_id=user_id,
        content=content,
        event_type="rating",
        session_id=session_id,
        app_version=app_version,
        model=model,
        lang=lang,
    )

def log_chat_message(
    user_id: str,
    *,
    session_id: Optional[str],
    role: str,
    content: str,
    lang: str = "العربية",
    model: Optional[str] = None,
    app_version: Optional[str] = None,
    streaming: bool = False,
    extra: Optional[Dict[str, Any]] = None,
    **_
) -> None:
    payload = {
        "role": role,
        "text": str(content or ""),
        "streaming": bool(streaming),
        "extra": _safe(extra or {}),
    }
    log_user_insight(
        user_id=user_id,
        content=payload,
        event_type="chat_interaction",
        session_id=session_id,
        app_version=app_version,
        model=model,
        lang=lang,
    )
