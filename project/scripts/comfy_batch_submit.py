#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
يرسل دفعة Jobs (ملفات Workflow JSON من ComfyUI "Save (API)") إلى API
ويحمّل المخرجات (صور/فيديو) إلى مجلد outputs.

usage:
  COMFY=http://127.0.0.1:8188 python comfy_batch_submit.py --jobs ../jobs --out ../outputs
options:
  --jobs   مسار ملف JSON واحد أو مجلد فيه عدة JSON.
  --out    مجلد المخرجات (سيُنشأ لو غير موجود).
  --tag    وسم/بادئة لاسم الملفات الناتجة (اختياري).

ملاحظات:
- ملفات الـ JSON إما تحتوي مفتاح "prompt" أو تكون هي الـ prompt مباشرة.
- يعتمد على واجهة ComfyUI: /prompt ثم polling على /history/{prompt_id}
- تنزيل الملفات عبر /view?filename=...&subfolder=...&type=output
"""

import os, sys, json, time, argparse, pathlib, re
from typing import Dict, Any, List
import requests
from tqdm import tqdm

DEFAULT_COMFY = os.environ.get("COMFY", "http://127.0.0.1:8188")
POLL_SEC = float(os.environ.get("POLL_SEC", "1.2"))
REQ_TIMEOUT = int(os.environ.get("REQ_TIMEOUT", "30"))

def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

def find_jobs(path: str) -> List[pathlib.Path]:
    p = pathlib.Path(path)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted([x for x in p.glob("*.json") if x.is_file()], key=lambda x: natural_key(x.name))
    raise FileNotFoundError(f"Path not found: {path}")

def post_prompt(prompt: Dict[str, Any], comfy: str) -> str:
    r = requests.post(f"{comfy}/prompt", json={"prompt": prompt, "client_id": "batch"}, timeout=REQ_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data.get("prompt_id") or data.get("prompt") or data.get("id")

def get_history(prompt_id: str, comfy: str) -> Dict[str, Any]:
    r = requests.get(f"{comfy}/history/{prompt_id}", timeout=REQ_TIMEOUT)
    r.raise_for_status()
    return r.json().get(prompt_id, {})

def download_artifacts(hist: Dict[str, Any], out_dir: pathlib.Path, prefix: str, comfy: str) -> int:
    outputs = (hist.get("outputs") or {})
    saved = 0
    for node_id, node_out in outputs.items():
        # images
        for img in node_out.get("images", []):
            url = f'{comfy}/view?filename={img["filename"]}&subfolder={img.get("subfolder","")}&type={img.get("type","output")}'
            fn = f"{prefix}_{img['filename']}"
            save_to = out_dir / fn
            with requests.get(url, stream=True, timeout=REQ_TIMEOUT) as r:
                r.raise_for_status()
                with open(save_to, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            saved += 1
        # videos (بعض النودز ترجع videos)
        for vid in node_out.get("videos", []):
            url = f'{comfy}/view?filename={vid["filename"]}&subfolder={vid.get("subfolder","")}&type={vid.get("type","output")}'
            fn = f"{prefix}_{vid['filename']}"
            save_to = out_dir / fn
            with requests.get(url, stream=True, timeout=REQ_TIMEOUT) as r:
                r.raise_for_status()
                with open(save_to, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            saved += 1
    return saved

def ensure_out_subdirs(base_out: pathlib.Path) -> Dict[str, pathlib.Path]:
    base_out.mkdir(parents=True, exist_ok=True)
    (base_out / "images").mkdir(exist_ok=True)
    (base_out / "videos").mkdir(exist_ok=True)
    return {"images": base_out / "images", "videos": base_out / "videos"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True, help="ملف JSON أو مجلد JSON jobs")
    ap.add_argument("--out", required=True, help="مجلد المخرجات")
    ap.add_argument("--tag", default="", help="بادئة اختيارية لأسماء الملفات")
    ap.add_argument("--comfy", default=DEFAULT_COMFY, help="عنوان ComfyUI (افتراضي من COMFY)")
    args = ap.parse_args()

    comfy = args.comfy.rstrip("/")
    jobs = find_jobs(args.jobs)
    out_base = pathlib.Path(args.out).resolve()
    outs = ensure_out_subdirs(out_base)

    if not jobs:
        print("لا توجد ملفات JSON في --jobs", file=sys.stderr)
        sys.exit(1)

    for jpath in tqdm(jobs, desc="Submitting jobs"):
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            prompt = data.get("prompt", data)  # توافق
            prompt_id = post_prompt(prompt, comfy)
            # انتظار حتى تنتهي
            while True:
                h = get_history(prompt_id, comfy)
                status = ((h.get("status") or {}).get("status_str") or "").lower()
                if status in {"success", "failed"}:
                    break
                time.sleep(POLL_SEC)

            # حفظ المخرجات
            prefix = (args.tag + "_" if args.tag else "") + jpath.stem
            saved = download_artifacts(h, outs["images"], prefix, comfy)
            saved += download_artifacts(h, outs["videos"], prefix, comfy)
            # لو ما قدر يميّز نوع الملف، جرّب التنزيل إلى مجلد الأساس أيضًا
            if saved == 0:
                saved = download_artifacts(h, out_base, prefix, comfy)
            print(f"[OK] {jpath.name} -> saved {saved} files")
        except Exception as e:
            print(f"[ERR] {jpath.name}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
