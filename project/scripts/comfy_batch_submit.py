#!/usr/bin/env python3
import os, json, time, argparse, glob
import requests
from tqdm import tqdm

def post_prompt(base, workflow):
    r = requests.post(f"{base}/prompt", json=workflow, timeout=60)
    r.raise_for_status()
    return r.json().get("prompt_id")

def get_history(base, prompt_id):
    r = requests.get(f"{base}/history/{prompt_id}", timeout=60)
    if r.status_code == 200:
        return r.json()
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default="../jobs", help="Jobs dir (workflow JSON)")
    ap.add_argument("--out",  default="../outputs", help="Outputs dir")
    ap.add_argument("--base", default=os.environ.get("COMFY","http://127.0.0.1:8188"), help="ComfyUI base URL")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    jobs = sorted(glob.glob(os.path.join(args.jobs, "*.json")))
    if not jobs:
        print("No jobs found in", args.jobs)
        return

    for jpath in tqdm(jobs, desc="Submitting jobs"):
        with open(jpath, "r", encoding="utf-8") as f:
            wf = json.load(f)

        # بعض الـ workflows تُحفظ عبر "Save (API)" مباشرة — استخدمها كما هي
        pid = post_prompt(args.base, wf)
        print("Submitted:", os.path.basename(jpath), "| pid:", pid)

        # انتظار نتايج بسيطة (اختياري)
        for _ in range(240):  # ~240 * 1s = 4 دقائق
            h = get_history(args.base, pid)
            # إذا احتجت تحفظ مخرجات الصور/الفيديو من مسارات ComfyUI، عدّل هنا حسب الـ nodes
            if h:
                break
            time.sleep(1)

    print("Done. Check", args.out)

if __name__ == "__main__":
    main()
