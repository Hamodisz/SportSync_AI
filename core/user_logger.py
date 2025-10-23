# -- coding: utf-8 --
"""Lightweight logging helpers: JSONL append always, optional SQLite mirror."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_LOG_DIR = Path("outputs/logs")
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_FILES = {
    "submissions": _LOG_DIR / "quiz_submissions.jsonl",
    "ratings": _LOG_DIR / "ratings.jsonl",
    "chat": _LOG_DIR / "chat.jsonl",
    "events": _LOG_DIR / "events.jsonl",
}

_DB_PATH = Path("data/sportsync.db")
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_SQLITE_AVAILABLE = sqlite3 is not None
_DB_LOCK = threading.RLock()


def _utc_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def _ensure_sqlite() -> Optional[sqlite3.Connection]:
    if not _SQLITE_AVAILABLE:
        return None
    try:
        conn = sqlite3.connect(_DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_submissions (
                id TEXT PRIMARY KEY,
                ts TEXT,
                user_id TEXT,
                session_id TEXT,
                lang TEXT,
                answers_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                id TEXT PRIMARY KEY,
                ts TEXT,
                user_id TEXT,
                session_id TEXT,
                idx INTEGER,
                rating INTEGER,
                lang TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat (
                id TEXT PRIMARY KEY,
                ts TEXT,
                user_id TEXT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                lang TEXT,
                extra_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                ts TEXT,
                user_id TEXT,
                session_id TEXT,
                name TEXT,
                payload_json TEXT,
                lang TEXT
            )
            """
        )
        conn.commit()
        return conn
    except Exception as exc:  # pragma: no cover
        print("[LOGGER] sqlite init failed", exc)
        return None


_SQL_CONN = _ensure_sqlite()


def _insert_sql(table: str, row: Dict[str, Any]) -> None:
    if _SQL_CONN is None:
        return
    with _DB_LOCK:
        try:
            columns = ",".join(row.keys())
            placeholders = ":" + ",:".join(row.keys())
            _SQL_CONN.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", row)
            _SQL_CONN.commit()
        except Exception as exc:  # pragma: no cover
            print("[LOGGER] sqlite insert failed", exc)


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
    try:
        _append_jsonl(_FILES["submissions"], payload)
    except Exception as exc:
        print("[LOGGER] JSONL write failed (submissions)", exc)
    _insert_sql(
        "quiz_submissions",
        {
            "id": entry_id,
            "ts": payload["ts"],
            "user_id": user_id,
            "session_id": session_id,
            "lang": lang,
            "answers_json": json.dumps(answers, ensure_ascii=False),
        },
    )
    return entry_id


def log_rating(user_id: str, session_id: str, index: int, rating: int, lang: str) -> None:
    entry_id = str(uuid.uuid4())
    payload = {
        "id": entry_id,
        "ts": _utc_now(),
        "user_id": user_id,
        "session_id": session_id,
        "idx": index,
        "rating": rating,
        "lang": lang,
    }
    try:
        _append_jsonl(_FILES["ratings"], payload)
    except Exception as exc:
        print("[LOGGER] JSONL write failed (ratings)", exc)
    _insert_sql("ratings", payload)


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
        _append_jsonl(_FILES["chat"], payload)
    except Exception as exc:
        print("[LOGGER] JSONL write failed (chat)", exc)
    _insert_sql(
        "chat",
        {
            "id": entry_id,
            "ts": payload["ts"],
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "lang": lang,
            "extra_json": json.dumps(extra or {}, ensure_ascii=False),
        },
    )


def log_event(
    user_id: str,
    session_id: str,
    name: str,
    payload: Optional[Dict[str, Any]] = None,
    lang: str = "ar",
) -> None:
    entry_id = str(uuid.uuid4())
    data = {
        "id": entry_id,
        "ts": _utc_now(),
        "user_id": user_id,
        "session_id": session_id,
        "name": name,
        "payload": payload or {},
        "lang": lang,
    }
    try:
        _append_jsonl(_FILES["events"], data)
    except Exception as exc:
        print("[LOGGER] JSONL write failed (events)", exc)
    _insert_sql(
        "events",
        {
            "id": entry_id,
            "ts": data["ts"],
            "user_id": user_id,
            "session_id": session_id,
            "name": name,
            "payload_json": json.dumps(payload or {}, ensure_ascii=False),
            "lang": lang,
        },
    )


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception as exc:
        print("[LOGGER] count_lines failed", path, exc)
        return 0


def _sqlite_counts() -> Dict[str, int]:
    if _SQL_CONN is None:
        return {}
    counts: Dict[str, int] = {}
    with _DB_LOCK:
        try:
            cur = _SQL_CONN.cursor()
            for table in ("quiz_submissions", "ratings", "chat", "events"):
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
        except Exception as exc:
            print("[LOGGER] sqlite count failed", exc)
    return counts


def get_log_stats() -> Dict[str, Any]:
    stats = {
        "files": {
            "submissions": _count_lines(_FILES["submissions"]),
            "ratings": _count_lines(_FILES["ratings"]),
            "chat": _count_lines(_FILES["chat"]),
            "events": _count_lines(_FILES["events"]),
        }
    }
    sqlite_counts = _sqlite_counts()
    if sqlite_counts:
        stats["sqlite"] = sqlite_counts
    return stats
