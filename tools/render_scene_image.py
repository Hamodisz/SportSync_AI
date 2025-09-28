cat > tools/render_scene_image.py <<'PY'
import os, json, base64, requests, pathlib

ENDPOINT = os.getenv("RUNPOD_ENDPOINT_ID")
API_KEY  = os.getenv("RUNPOD_API_KEY")

def generate_image(prompt, out_path, width=1080, height=1920, seed=123456789):
    if not ENDPOINT or not API_KEY:
        raise RuntimeError("RUNPOD_ENDPOINT_ID / RUNPOD_API_KEY missing")

    wf = {
      "30":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"flux1-dev-fp8.safetensors"}},
      "27":{"class_type":"EmptySD3LatentImage","inputs":{"width":width,"height":height,"batch_size":1}},
      "6":{"class_type":"CLIPTextEncode","inputs":{"text":prompt,"clip":["30",1]}},
      "35":{"class_type":"FluxGuidance","inputs":{"guidance":3.5,"conditioning":["6",0]}},
      "33":{"class_type":"CLIPTextEncode","inputs":{"text":"","clip":["30",1]}},
      "31":{"class_type":"KSampler","inputs":{
          "seed":seed,"steps":10,"cfg":1,"sampler_name":"euler","scheduler":"simple","denoise":1,
          "model":["30",0],"positive":["35",0],"negative":["33",0],"latent_image":["27",0]}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["31",0],"vae":["30",2]}}
    }

    url = f"https://api.runpod.ai/v2/{ENDPOINT}/runsync"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type":"application/json"}
    payload = {"input":{"workflow": wf}}
    r = requests.post(url, headers=headers, json=payload, timeout=900)
    r.raise_for_status()
    resp = r.json()
    b64 = resp["output"]["images"][0]["data"]
    out = pathlib.Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(b64))
    return str(out)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    args = p.parse_args()
    print(generate_image(args.prompt, args.out, args.width, args.height))
PY
