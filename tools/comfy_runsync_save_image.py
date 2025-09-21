import os, json, base64, argparse, requests, sys

parser = argparse.ArgumentParser()
parser.add_argument("--workflow", required=True)
parser.add_argument("--prompt", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()

api_key = os.environ.get("RUNPOD_API_KEY")
endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")
if not api_key or not endpoint_id:
    print("Missing RUNPOD_API_KEY or RUNPOD_ENDPOINT_ID"); sys.exit(1)

with open(args.workflow, "r", encoding="utf-8") as f:
    wf = json.load(f)

# حاول نحدّث نص البرومبت في عقدة CLIPTextEncode رقم "6"
try:
    wf["input"]["workflow"]["6"]["inputs"]["text"] = args.prompt
except Exception:
    pass

url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
resp = requests.post(url, headers=headers, json=wf, timeout=600)
resp.raise_for_status()
data = resp.json()

imgs = data.get("output", {}).get("images", [])
if not imgs:
    print("No images in response:", data); sys.exit(2)

img_bytes = base64.b64decode(imgs[0]["data"])
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
with open(args.out, "wb") as f:
    f.write(img_bytes)
print("Saved:", args.out)
