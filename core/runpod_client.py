# -- coding: utf-8 --
import os, json, base64, requests
from dotenv import load_dotenv

# يقرأ متغيرات البيئة من .env
load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
ENDPOINT_ID    = os.getenv("RUNPOD_COMFY_ENDPOINT_ID")

if not RUNPOD_API_KEY or not ENDPOINT_ID:
    raise RuntimeError("Set RUNPOD_API_KEY and RUNPOD_COMFY_ENDPOINT_ID in your environment / .env")

def comfy_runsync(workflow: dict, timeout_sec: int = 600):
    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": {"workflow": workflow}}
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout_sec)
    r.raise_for_status()
    return r.json()
