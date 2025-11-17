# -- coding: utf-8 --
"""
server.py
---------
واجهات REST بسيطة:
- POST /api/jobs                 → إنشاء Job جديد للتحليل
- GET  /api/jobs/{job_id}        → حالة التحليل
- GET  /api/recommendations/{id} → النتيجة (cards) عند الجاهزية

تشغيل محلي:
  uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from src.analysis.deferred_analysis import create_job, get_status, get_result

app = FastAPI(title="SportSync API", version="1.0")

class JobRequest(BaseModel):
    answers: Dict[str, Any]
    lang: Optional[str] = "العربية"
    user_id: Optional[str] = None

@app.post("/api/jobs")
def api_create_job(req: JobRequest):
    try:
        job = create_job(answers=req.answers or {}, lang=req.lang or "العربية", user_id=req.user_id)
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
def api_job_status(job_id: str):
    st = get_status(job_id)
    if not st:
        raise HTTPException(status_code=404, detail="job_id not found")
    return st

@app.get("/api/recommendations/{job_id}")
def api_job_result(job_id: str):
    st = get_status(job_id)
    if not st:
        raise HTTPException(status_code=404, detail="job_id not found")
    if st.get("status") != "done":
        return {"status": st.get("status"), "progress": st.get("progress", 0)}
    res = get_result(job_id)
    if not res:
        raise HTTPException(status_code=404, detail="result not found")
    return {"status": "done", **res}
