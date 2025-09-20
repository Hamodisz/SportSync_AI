# coding: utf-8
"""
tools/comfy_serverless.py
Simple client for RunPod Serverless ComfyUI worker.
- Reads RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID from env.
- Submits a workflow JSON (dict), polls status, saves images.
Usage:
  export RUNPOD_API_KEY=...
  export RUNPOD_ENDPOINT_ID=...
  python tools/comfy_serverless.py --prompt "sport identity, stealth-flow, dramatic light" --out ./outputs/comfy --count 1
"""

import os, sys, json, time, base64, argparse, pathlib
import requests

API_BASE = "https://api.runpod.ai/v2"

API_KEY = os.getenv("RUNPOD_API_KEY", "")
ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "")

def _assert_env():
    if not API_KEY or not ENDPOINT_ID:
        raise SystemExit("Please set RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID env vars.")

def _headers():
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def _endpoint_url(path: str) -> str:
    return f"{API_BASE}/{ENDPOINT_ID}{path}"

def submit_job(workflow: dict) -> str:
    """POST /run -> returns jobId"""
    url = _endpoint_url("/run")
    payload = {"input": {"workflow": workflow}}
    r = requests.post(url, headers=_headers(), json=payload, timeout=300)
    r.raise_for_status()
    data = r.json()
    job_id = data.get("id") or data.get("jobId") or data.get("data", {}).get("id")
    if not job_id:
        raise RuntimeError(f"Cannot find job id in response: {data}")
    return job_id

def poll_status(job_id: str, interval_s: float = 2.0, max_wait_s: float = 900.0) -> dict:
    """GET /status/{job_id} until COMPLETED/FAILED"""
    url = _endpoint_url(f"/status/{job_id}")
    t0 = time.time()
    while True:
        r = requests.get(url, headers=_headers(), timeout=120)
        r.raise_for_status()
        data = r.json()
        s = (data.get("status") or data.get("state") or "").upper()
        if s in ("COMPLETED", "SUCCEEDED", "SUCCESS"):
            return data
        if s in ("FAILED", "ERROR"):
            raise RuntimeError(f"Job failed: {json.dumps(data)[:800]}")
        if time.time() - t0 > max_wait_s:
            raise TimeoutError("Polling timed out.")
        time.sleep(interval_s)

def _ensure_dir(p: str) -> str:
    d = pathlib.Path(p)
    d.mkdir(parents=True, exist_ok=True)
    return str(d)

def _extract_images(result: dict) -> list[bytes]:
    """
    ComfyUI worker returns images in different shapes:
    - result['output']['images'] -> list of dicts with base64 under 'image' or 'data'
    - sometimes nested under result['output']['result']['images']
    We normalize and return a list of raw PNG/JPG bytes.
    """
    out = result.get("output") or {}
    imgs = out.get("images")
    if imgs is None and isinstance(out.get("result"), dict):
        imgs = out["result"].get("images")

    payloads = []
    if isinstance(imgs, list):
        for it in imgs:
            b64 = it.get("image") or it.get("data") or it.get("b64")
            if b64:
                # strip data URL header if present
                if "," in b64 and b64.strip().startswith("data:"):
                    b64 = b64.split(",", 1)[1]
                payloads.append(base64.b64decode(b64))
    return payloads

def run_prompt(prompt: str, out_dir: str, count: int = 1, seed: int | None = None,
               width: int = 768, height: int = 1024) -> list[str]:
    """
    Build a minimal Flux1 workflow and run it.
    Returns list of saved file paths.
    """
    # Minimal text2img workflow (Flux1-dev fp8) – vertical 768x1024
    wf = {
        "6":  {"inputs":{"text": prompt, "clip": ["30", 1]}, "class_type":"CLIPTextEncode"},
        "33": {"inputs":{"text": "", "clip": ["30", 1]}, "class_type":"CLIPTextEncode"},
        "27": {"inputs":{"width": width, "height": height, "batch_size": max(1, count)},
               "class_type":"EmptySD3LatentImage"},
        "30": {"inputs":{"ckpt_name": "flux1-dev-fp8.safetensors"}, "class_type":"CheckpointLoaderSimple"},
        "35": {"inputs":{"guidance": 3.5, "conditioning": ["6", 0]}, "class_type":"FluxGuidance"},
        "31": {"inputs":{
                    "seed": seed if seed is not None else 42,
                    "steps": 12, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1,
                    "model": ["30", 0], "positive": ["35", 0], "negative": ["33", 0], "latent_image": ["27", 0]
               }, "class_type":"KSampler"},
        "8":  {"inputs":{"samples": ["31", 0], "vae": ["30", 2]}, "class_type":"VAEDecode"},
        "40": {"inputs":{"filename_prefix": "ComfyUI", "images": ["8", 0]}, "class_type":"SaveImage"}
    }

    job_id = submit_job(wf)
    result = poll_status(job_id)
    raws = _extract_images(result)
    out_dir = _ensure_dir(out_dir)
    paths = []
    for i, blob in enumerate(raws, 1):
        fn = os.path.join(out_dir, f"comfy_{int(time.time())}_{i:02d}.png")
        with open(fn, "wb") as f:
            f.write(blob)
        paths.append(fn)
    return paths

def main():
    _assert_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", default="./outputs/comfy")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--w", type=int, default=768)
    ap.add_argument("--h", type=int, default=1024)
    args = ap.parse_args()

    paths = run_prompt(args.prompt, args.out, count=args.count, seed=args.seed, width=args.w, height=args.h)
    print("\nSaved:")
    for p in paths:
        print(" -", p)

if __name__ == "__main__":
    main()
