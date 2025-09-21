import os, json, base64, requests
from pathlib import Path

# ==========[ عدّل هذي الثلاثة ]==========
ENDPOINT_ID = "ضع-هنا-Endpoint-ID"     # مثال: v2swa6f8zzcjk... (انسخه من صفحة السيرفرلس)
PROMPT = "a cinematic corgi portrait, soft light, high detail"
OUT_PATH = Path("content_studio/ai_images/outputs/scene_01.png")
# =======================================

API_KEY = os.getenv("RUNPOD_API_KEY")  # حط المفتاح كمتغير بيئة (تحت بيّن لك كيف)
URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

payload = {
    "input": {
        "workflow": {
            "30": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"}
            },
            "27": {
                "class_type": "EmptySD3LatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": PROMPT, "clip": ["30", 1]}
            },
            "35": {
                "class_type": "FluxGuidance",
                "inputs": {"guidance": 3.5, "conditioning": ["6", 0]}
            },
            "33": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "", "clip": ["30", 1]}
            },
            "31": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 123456789,
                    "steps": 10,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["30", 0],
                    "positive": ["35", 0],
                    "negative": ["33", 0],
                    "latent_image": ["27", 0]
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["31", 0], "vae": ["30", 2]}
            },
            "40": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "comfyui", "images": ["8", 0]}
            }
        }
    }
}

def main():
    if not API_KEY:
        raise SystemExit("RUNPOD_API_KEY is not set. Please set your API key in env vars.")

    r = requests.post(URL, headers=HEADERS, data=json.dumps(payload), timeout=600)
    r.raise_for_status()
    data = r.json()

    if "output" not in data or "images" not in data["output"]:
        print(json.dumps(data, indent=2))
        raise SystemExit("No images in response.")

    img_b64 = data["output"]["images"][0]["data"]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(base64.b64decode(img_b64))

    print(f"Saved: {OUT_PATH.resolve()}")

if __name__ == "__main__":
    main()
