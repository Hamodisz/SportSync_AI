# file: content_studio/ai_video/tools/runpod_gen.py
import os, json, time, base64, pathlib, requests, sys

def load_cfg(client: str):
    p = pathlib.Path(f"content_studio/assets/{client}/config.json")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_png(b64_str: str, path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(base64.b64decode(b64_str))

def main():
    client = os.environ.get("CLIENT")
    if not client:
        print("CLIENT env is required"); sys.exit(1)

    api_key = os.environ.get("RUNPOD_API_KEY")
    endpoint = os.environ.get("RUNPOD_ENDPOINT_ID")
    base_url = os.environ.get("RUNPOD_BASE_URL", "https://api.runpod.ai")

    if not api_key or not endpoint:
        print("RUNPOD_API_KEY / RUNPOD_ENDPOINT_ID are required"); sys.exit(1)

    cfg = load_cfg(client)
    scenes = cfg.get("scenes", [])
    if not scenes:
        print("No scenes in config"); sys.exit(1)

    # نبني قائمة برومبتات من النصوص (عدلها حسب فلود ComfyUI عندك)
    prompts = []
    for i, s in enumerate(scenes, start=1):
        txt = s.get("text", "") or f"scene {i}"
        prompts.append(txt)

    # 1) نرسل جوب لتوليد صور – عدّل الـpayload حسب نقطة ComfyUI/النموذج عندك
    payload = {
        "input": {
            "prompts": prompts,
            # أي بارامترات أخرى يحتاجها الفلو (CFG, steps, model, size...)
            "width": 1080,
            "height": 1920
        }
    }

    r = requests.post(
        f"{base_url}/v2/{endpoint}/run",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload, timeout=60
    )
    r.raise_for_status()
    job_id = r.json()["id"]
    print("RunPod job:", job_id)

    # 2) نستعلم لين يخلص
    while True:
        s = requests.get(
            f"{base_url}/v2/{endpoint}/status/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )
        s.raise_for_status()
        js = s.json()
        st = js.get("status")
        if st in ("COMPLETED", "FAILED", "CANCELLED"):
            result = js
            break
        time.sleep(2)

    if result.get("status") != "COMPLETED":
        print("RunPod failed:", result); sys.exit(1)

    # 3) نحفظ الصور
    outdir = pathlib.Path(f"content_studio/assets/{client}/images")
    outdir.mkdir(parents=True, exist_ok=True)

    # توقّع أن الناتج يكون base64 تحت output.images أو روابط URLs تحت output.urls
    output = result.get("output", {})
    images_b64 = output.get("images") or []
    images_urls = output.get("urls") or []

    saved = []
    if images_b64:
        for i, b64 in enumerate(images_b64, start=1):
            p = outdir / f"scene_{i}.png"
            save_png(b64, p)
            saved.append(str(p))
    elif images_urls:
        for i, u in enumerate(images_urls, start=1):
            p = outdir / f"scene_{i}.png"
            img = requests.get(u, timeout=60)
            img.raise_for_status()
            p.write_bytes(img.content)
            saved.append(str(p))
    else:
        print("No images field in RunPod output"); sys.exit(1)

    print("Saved images:", saved)

if __name__ == "__main__":
    main()
