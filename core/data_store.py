# core/data_store.py
# -- coding: utf-8 --
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Dict

ROOT = Path("/tmp/sportsync_v1")  # على Render مؤقت؛ لاحقاً نربط S3/DB
LOG = ROOT / "events.jsonl"
ROOT.mkdir(parents=True, exist_ok=True)

def log_event(kind: str, data: Dict):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": time.time(), "kind": kind, "data": data}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
