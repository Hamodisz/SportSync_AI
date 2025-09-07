# -- coding: utf-8 --
"""
core/deferred_analysis.py
-------------------------
طبقة "وظائف مؤجّلة" لتحليل الهوية الرياضية وإرجاع رابط متابعة + رابط نتيجة.
- create_job(...)  → ينشئ job_id ويبدأ ثريد خلفي للتحليل
- get_status(job_id) → حالة التحليل (queued / running / done / error)
- get_result(job_id) → يعيد الكروت عند اكتمال التحليل

المزايا:
- رابط حالة ونتيجة مبني على base_url من الإعدادات أو APP_BASE_URL
- تخزين نتائج كل Job في data/jobs/<job_id>.json (تحمّل سريع عند الرجوع)
- تليمتري اختيارية عبر core.data_pipe (Zapier/Webhook/Disk)
- آمن للخيوط (thread-safe) وبسيط

الاعتمادات:
- يعتمد على core.backend_gpt.generate_sport_recommendation
- core.app_config.get_config للحصول على base_url إن وُجد
"""

from __future__ import annotations
import os, json, uuid, time, threading, pathlib, traceback
from typing import Any, Dict, Optional, Tuple

# مسارات التخزين
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = (ROOT / "data").resolve()
JOBS_DIR = (DATA_DIR / "jobs").resolve()
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# الإعدادات
try:
    from core.app_config import get_config
    CFG = get_config()
except Exception:
    CFG = {}

BASE_URL = (
    (CFG.get("app") or {}).get("base_url") or
    os.getenv("APP_BASE_URL") or
    "https://sportsync.ai"
).rstrip("/")

# تليمتري (اختياري)
try:
    from core.data_pipe import get_pipe
    _PIPE = get_pipe()
except Exception:
    _PIPE = None

# منطق التحليل
from core.backend_gpt import generate_sport_recommendation  # type: ignore

# حالة الـ Jobs بالذاكرة + قفل
_LOCK = threading.RLock()
_JOBS: Dict[str, Dict[str, Any]] = {}  # job_id -> state


def _now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.utcnow().isoformat() + "Z"


def _job_paths(job_id: str) -> Tuple[pathlib.Path, pathlib.Path]:
    meta = JOBS_DIR / f"{job_id}.meta.json"
    result = JOBS_DIR / f"{job_id}.result.json"
    return meta, result


def _persist_meta(job_id: str) -> None:
    meta_p, _ = _job_paths(job_id)
    with _LOCK:
        meta = _JOBS.get(job_id, {}).copy()
    try:
        with meta_p.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _persist_result(job_id: str, cards: Any) -> None:
    _, res_p = _job_paths(job_id)
    try:
        with res_p.open("w", encoding="utf-8") as f:
            json.dump({"cards": cards}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_result(job_id: str) -> Optional[Dict[str, Any]]:
    _, res_p = _job_paths(job_id)
    if not res_p.exists():
        return None
    try:
        with res_p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _send_pipe(event_type: str, payload: Dict[str, Any]) -> None:
    if not _PIPE:
        return
    try:
        _PIPE.send(event_type=event_type, payload=payload, user_id=str(payload.get("user_id","anon")),
                   session_id=str(payload.get("job_id","")), lang=str(payload.get("lang","العربية")),
                   model="")
    except Exception:
        pass


def _build_urls(job_id: str, lang: str) -> Dict[str, str]:
    status_url = f"{BASE_URL}/api/jobs/{job_id}"
    result_url = f"{BASE_URL}/api/recommendations/{job_id}"
    share_url  = f"{BASE_URL}/recommendation?job={job_id}&lang={('ar' if lang=='العربية' else 'en')}"
    return {"status_url": status_url, "result_url": result_url, "share_url": share_url}


def _worker(job_id: str) -> None:
    # يشتغل بالخلفية
    with _LOCK:
        job = _JOBS.get(job_id, {})
        user_id = job.get("user_id", "anon")
        lang = job.get("lang", "العربية")
        answers = job.get("answers", {})
        _JOBS[job_id]["status"] = "running"
        _JOBS[job_id]["progress"] = 10
        _JOBS[job_id]["updated_at"] = _now_iso()
    _persist_meta(job_id)
    _send_pipe("job_started", {"job_id": job_id, "user_id": user_id, "lang": lang})

    try:
        # التحليل الحقيقي (قد يأخذ وقت)
        cards = generate_sport_recommendation(answers=answers, lang=lang, user_id=user_id, job_id=job_id)  # type: ignore
        # خزّن النتيجة
        _persist_result(job_id, cards)

        with _LOCK:
            _JOBS[job_id]["status"] = "done"
            _JOBS[job_id]["progress"] = 100
            _JOBS[job_id]["updated_at"] = _now_iso()
            _JOBS[job_id]["completed_at"] = _now_iso()
        _persist_meta(job_id)
        _send_pipe("job_completed", {"job_id": job_id, "user_id": user_id, "lang": lang})
    except Exception as e:
        err = f"{e}"
        tb = traceback.format_exc(limit=2)
        with _LOCK:
            _JOBS[job_id]["status"] = "error"
            _JOBS[job_id]["error"] = err
            _JOBS[job_id]["updated_at"] = _now_iso()
        _persist_meta(job_id)
        _send_pipe("job_failed", {"job_id": job_id, "user_id": user_id, "lang": job.get("lang","العربية"), "error": err, "trace": tb})


def create_job(answers: Dict[str, Any], lang: str = "العربية", user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    ينشئ Job جديد ويعيد: {job_id, status_url, result_url, share_url, status}
    """
    job_id = uuid.uuid4().hex[:12]
    if not user_id:
        user_id = uuid.uuid4().hex

    urls = _build_urls(job_id, lang)
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "user_id": user_id,
            "lang": lang,
            "answers": answers or {},
            "status": "queued",
            "progress": 0,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            **urls
        }
    _persist_meta(job_id)
    _send_pipe("job_created", {"job_id": job_id, "user_id": user_id, "lang": lang})

    # شغّل الثريد
    t = threading.Thread(target=_worker, args=(job_id,), daemon=True)
    t.start()

    return {
        "job_id": job_id,
        "status": "queued",
        **urls
    }


def get_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    حالة الوظيفة. يعيد None إن لم يوجد job.
    """
    with _LOCK:
        meta = _JOBS.get(job_id)
    if meta:
        return {k: v for k, v in meta.items() if k != "answers"}
    # إن لم تكن بالذاكرة، جرّب التحميل من الملف (في حال إعادة التشغيل)
    meta_p, _ = _job_paths(job_id)
    if meta_p.exists():
        try:
            with meta_p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def get_result(job_id: str) -> Optional[Dict[str, Any]]:
    """
    يعيد {"cards": [...]} إن كانت الحالة done.
    """
    status = get_status(job_id)
    if not status:
        return None
    if status.get("status") != "done":
        return None
    return _load_result(job_id)
