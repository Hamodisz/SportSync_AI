# -- coding: utf-8 --
"""Durable user logging: JSON snapshot + CSV index + JSONL event streams."""
from __future__ import annotations

import csv
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_LOG_LOCK = threading.RLock()

_QUIZ_DIR = Path("outputs/quiz_submissions")
_QUIZ_DIR.mkdir(parents=True, exist_ok=True)
_QUIZ_CSV = _QUIZ_DIR / "index.csv"

_EVENTS_DIR = Path("outputs/events")
_EVENTS_DIR.mkdir(parents=True, exist_ok=True)
_EVENT_FILES = {
    "ratings": _EVENTS_DIR / "ratings.jsonl",
    "chat": _EVENTS_DIR / "chat.jsonl",
    "events": _EVENTS_DIR / "events.jsonl",
}

_BANNED_TERMS = ()  # kept for future processing hooks


def _utc_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()


def _write_session_snapshot(session_id: str, payload: Dict[str, Any]) -> None:
    session_file = _QUIZ_DIR / f"{session_id}.json"
    entries = []
    if session_file.exists():
        try:
            entries = json.loads(session_file.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(payload)
    tmp_path = session_file.with_suffix(session_file.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)
    tmp_path.replace(session_file)


def _append_csv_row(row: Dict[str, Any]) -> None:
    _QUIZ_DIR.mkdir(parents=True, exist_ok=True)
    file_exists = _QUIZ_CSV.exists()
    with _QUIZ_CSV.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        if not file_exists:
            writer.writerow(["id", "ts", "user_id", "session_id", "lang", "answers_json", "meta_json"])
        writer.writerow([
            row["id"],
            row["ts"],
            row["user_id"],
            row["session_id"],
            row["lang"],
            json.dumps(row["answers"], ensure_ascii=False),
            json.dumps(row.get("meta", {}), ensure_ascii=False),
        ])


def log_quiz_submission(
    user_id: str,
    answers: Dict[str, Any],
    lang: str,
    session_id: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    entry_id = str(uuid.uuid4())
    payload = {
        "id": entry_id,
        "ts": _utc_now(),
        "user_id": user_id,
        "session_id": session_id,
        "lang": lang,
        "answers": answers,
        "meta": meta or {},
    }
    with _LOG_LOCK:
        try:
            _write_session_snapshot(session_id, payload)
        except Exception as exc:
            print("[LOGGER] failed to write session snapshot", exc)
        try:
            _append_csv_row(payload)
        except Exception as exc:
            print("[LOGGER] failed to append quiz CSV", exc)
    return entry_id


def log_rating(user_id: str, session_id: str, index: int, rating: int, lang: str) -> None:
    entry_id = str(uuid.uuid4())
    payload = {
        "id": entry_id,
        "ts": _utc_now(),
        "user_id": user_id,
        "session_id": session_id,
        "index": index,
        "rating": rating,
        "lang": lang,
    }
    try:
        _append_jsonl(_EVENT_FILES["ratings"], payload)
    except Exception as exc:
        print("[LOGGER] failed to append rating", exc)


def log_chat_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    lang: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    entry_id = str(uuid.uuid4())
    payload = {
        "id": entry_id,
        "ts": _utc_now(),
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "lang": lang,
        "extra": extra or {},
    }
    try:
        _append_jsonl(_EVENT_FILES["chat"], payload)
    except Exception as exc:
        print("[LOGGER] failed to append chat message", exc)


def log_event(
    user_id: str,
    session_id: str,
    name: str,
    payload: Optional[Dict[str, Any]] = None,
    lang: str = "ar",
) -> None:
    entry_id = str(uuid.uuid4())
    record = {
        "id": entry_id,
        "ts": _utc_now(),
        "user_id": user_id,
        "session_id": session_id,
        "name": name,
        "payload": payload or {},
        "lang": lang,
    }
    try:
        _append_jsonl(_EVENT_FILES["events"], record)
    except Exception as exc:
        print("[LOGGER] failed to append event", exc)


def log_recommendation_result(session_id: str, payload: Dict[str, Any]) -> None:
    """Persist recommendation snapshots under data/logs for auditing and QA."""
    try:
        target_dir = Path('data/logs')
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_session = session_id or 'anon'
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
        path_obj = target_dir / f'{safe_session}_{ts}.json'
        with path_obj.open('w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        print('[LOGGER] failed to persist recommendation snapshot', exc)


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8") as fh:
            lines = sum(1 for _ in fh)
        return max(0, lines - 1)  # subtract header
    except Exception as exc:
        print("[LOGGER] failed to count csv rows", exc)
        return 0


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8") as fh:
            return sum(1 for _ in fh)
    except Exception as exc:
        print("[LOGGER] failed to count jsonl", exc)
        return 0


def get_log_stats() -> Dict[str, Any]:
    submissions = _count_csv_rows(_QUIZ_CSV)
    ratings = _count_jsonl(_EVENT_FILES["ratings"])
    chat_msgs = _count_jsonl(_EVENT_FILES["chat"])
    events = _count_jsonl(_EVENT_FILES["events"])
    return {
        "files": {
            "submissions": submissions,
            "ratings": ratings,
            "chat": chat_msgs,
            "events": events,
        }
    }


def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "insight") -> None:
    """Log user insights for analysis and tracking."""
    try:
        # تنظيف البيانات من أي objects غير قابلة للتحويل لـ JSON
        def clean_data(obj):
            """تحويل البيانات لشكل قابل للتسلسل JSON"""
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, dict):
                return {str(k): clean_data(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [clean_data(item) for item in obj]
            elif isinstance(obj, slice):
                # تحويل slice objects لـ string
                return f"slice({obj.start}:{obj.stop}:{obj.step})"
            else:
                # أي object آخر نحوله لـ string
                return str(obj)
        
        cleaned_content = clean_data(content)
        
        payload = {
            "user_id": user_id,
            "event_type": event_type,
            "content": cleaned_content,
        }
        log_event(
            user_id=user_id,
            session_id=cleaned_content.get("session_id", "unknown"),
            name=event_type,
            payload=cleaned_content,
            lang=cleaned_content.get("lang", "ar")
        )
    except Exception as exc:
        print(f"[LOGGER] failed to log user insight: {exc}")
