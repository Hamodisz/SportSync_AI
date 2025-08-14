# app_streamlit.py
# Streamlit UI — يشغّل التوليد في الخلفية ويعرض الفيديو عند جهوزه

import os, json, time, threading, uuid
from pathlib import Path
import streamlit as st

from core.core_engine import run_full_generation, quick_diagnose

# ممرات الإخراج (نفس اللي في core)
IMAGES_DIR = Path("content_studio/ai_images/outputs")
VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
FINAL_DIR  = Path("content_studio/ai_video/final_videos")
for p in (IMAGES_DIR, VOICE_PATH.parent, FINAL_DIR):
    p.mkdir(parents=True, exist_ok=True)

# إدارة أعمال الخلفية
JOBS_DIR = Path(".jobs"); JOBS_DIR.mkdir(exist_ok=True)
def _job_file(job_id: str) -> Path: return JOBS_DIR / f"{job_id}.json"
def _save_status(job_id: str, **data):
    _job_file(job_id).write_text(json.dumps({"job_id": job_id, **data}, ensure_ascii=False))
def _load_status(job_id: str):
    p = _job_file(job_id)
    return json.loads(p.read_text()) if p.exists() else {"job_id": job_id, "state": "missing"}

def _worker(job_id: str, params: dict):
    try:
        # توجيه خيارات الصور للصنعة الداخلية عبر متغيرات بيئية
        os.environ["USE_STOCK"]  = "1" if params.get("use_stock") else "0"
        os.environ["USE_OPENAI"] = "1" if params.get("use_openai") else "0"

        _save_status(job_id, state="running", msg="Generating...")
        result = run_full_generation(
            user_data={"topic":"sports motivation","traits":{"tone":"emotional"}},
            lang=params["lang"],
            image_duration=int(params["secs"]),
            override_script=params["script"],
            mute_if_no_voice=not params.get("add_voice", False),
            skip_cleanup=False,
        )
        if result.get("error"):
            _save_status(job_id, state="error", error=result["error"], result=result)
        else:
            _save_status(job_id, state="done", result=result)
    except Exception as e:
        _save_status(job_id, state="error", error=str(e))

def start_job(params: dict) -> str:
    job_id = uuid.uuid4().hex[:10]
    _save_status(job_id, state="queued", params=params)
    th = threading.Thread(target=_worker, args=(job_id, params), daemon=True)
    th.start()
    return job_id

# -------- UI --------
st.set_page_config(page_title="SportSync — Quick Video", layout="centered")
st.title("SportSync — Video + Personalizer (V1.2)")

DEFAULT_SCRIPT = """Title: Start your sport today

Scene 1: Sunrise over a quiet track — "Every beginning is a step."
Scene 2: Shoes hitting the ground — "Start with one simple move."
Scene 3: A calm smile — "Consistency beats perfection."
Outro: Give it 10 minutes today.
"""

lang  = st.selectbox("Language", ["en","ar"], index=0)
script = st.text_area("Script", DEFAULT_SCRIPT, height=230)
secs   = st.slider("Seconds per image", 2, 8, 4)

col1, col2, col3 = st.columns(3)
with col1:
    add_voice   = st.checkbox("Add voice-over", value=False)
with col2:
    use_openai  = st.checkbox("Use AI images (OpenAI)", value=False)
with col3:
    use_stock   = st.checkbox("Use stock photos (free)", value=True)

dbg = st.checkbox("Show debug (diagnose)", value=False)

cA, cB = st.columns([1,1])
go = cA.button("Generate video")
diag = cB.button("Quick diagnose")

if diag:
    st.json(quick_diagnose())

# زر “آخر فيديو” مفيد للاختبار
if st.button("Show latest video"):
    vids = sorted(FINAL_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if vids:
        st.success(f"Latest: {vids[0]}")
        st.video(str(vids[0]))
        with open(vids[0], "rb") as f:
            st.download_button("Download MP4", f, file_name=vids[0].name)
    else:
        st.info("لا توجد فيديوهات بعد.")

# إطلاق العمل في الخلفية
if go:
    params = dict(lang=lang, script=script, secs=secs,
                  add_voice=add_voice, use_openai=use_openai, use_stock=use_stock)
    st.session_state["job_id"] = start_job(params)
    st.info("بدأنا التوليد في الخلفية… انتظر ثواني وسيظهر التقدم هنا.")

# متابعة حالة العمل
job_id = st.session_state.get("job_id")
if job_id:
    st.write(f"Job: {job_id}")
    status = _load_status(job_id)
    state  = status.get("state")
    if state in {"queued","running"}:
        st.info("⏳ Generating images / voice / video…")
        st.progress(0 if state=="queued" else 60, text="Working… (page auto-refresh)")
        st.experimental_rerun()  # يُبقي الصفحة حيّة على Render
    elif state == "done":
        res = status.get("result", {})
        st.success("✅ Done!")
        if dbg: st.json(res)
        video = res.get("video")
        if video and Path(video).exists():
            st.video(video)
            with open(video, "rb") as f:
                st.download_button("Download MP4", f, file_name=Path(video).name)
        else:
            st.warning("الفيديو غير موجود على القرص بعد.")
    elif state == "error":
        st.error(f"ERROR: {status.get('error')}")
