# core/job_manager.py
# -*- coding: utf-8 -*-
import os, json, uuid, threading, time
from pathlib import Path

JOBS_DIR = Path(os.getenv("JOBS_DIR", "/tmp/sportsync_jobs"))
JOBS_DIR.mkdir(parents=True, exist_ok=True)

def _p(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"

def _write(job: dict) -> None:
    _p(job["id"]).write_text(json.dumps(job, ensure_ascii=False, indent=2), "utf-8")

def create_job(meta=None) -> dict:
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "status": "queued",        # queued | running | done | error
        "progress": 0,             # 0..100
        "created_at": time.time(),
        "updated_at": time.time(),
        "meta": meta or {},
        "note": "",
        "result": None,
        "error": None
    }
    _write(job)
    return job

def read_job(job_id: str) -> dict | None:
    p = _p(job_id)
    if not p.exists(): return None
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:
        return None

def update(job_id: str, **kw) -> dict:
    job = read_job(job_id) or {"id": job_id}
    job.update(kw)
    job["updated_at"] = time.time()
    _write(job)
    return job

def run_in_thread(job_id: str, target, *args, **kwargs):
    """يشغّل دالة التحليل في ثريد مستقل ويحدّث الحالة تلقائيًا."""
    def _wrap():
        try:
            update(job_id, status="running", progress=5, note="بدء التحليل…")
            result = target(*args, **kwargs, job_id=job_id)
            update(job_id, status="done", progress=100, note="اكتمل التحليل ✅", result=result)
        except Exception as e:
            update(job_id, status="error", progress=100, error=str(e), note="تعذّر التحليل")
    t = threading.Thread(target=_wrap, daemon=True)
    t.start()
    return t
