#!/usr/bin/env python3
import os, sys, json, base64, argparse, requests, pathlib

ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
API_KEY     = os.getenv("RUNPOD_API_KEY")

def load_workflow(path):
    with open(path, "r", encoding="utf-8") as f:
        wf = json.load(f)
    # تقبل الشكلين: {input:{workflow:{...}}} أو {workflow:{...}}
    if "input" in wf and "workflow" in wf["input"]:
        root = wf["input"]["workflow"]
        wrapper = wf  # كما هو
    elif "workflow" in wf:
        root = wf["workflow"]
        wrapper = {"input": {"workflow": root}}
    else:
        raise KeyError("workflow")
    return wrapper, root

def set_prompt(root, prompt_text):
    """
    يحاول إيجاد عقدة CLIPTextEncode ووضع النص.
    أولًا يبحث عن PLACEHOLDER، وإذا ما وجدها يكتب أول CLIPTextEncode.
    """
    target_key = None
    for k, node in root.items():
        if node.get("class_type") == "CLIPTextEncode":
            txt = node.get("inputs", {}).get("text", "")
            if isinstance(txt, str) and ("PLACEHOLDER" in txt or txt == "" or txt == "prompt"):
                target_key = k
                break
            if target_key is None:
                target_key = k  # أول واحدة احتياط
    if not target_key:
        raise KeyError("no CLIPTextEncode node found")
    root[target_key]["inputs"]["text"] = prompt_text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True, help="path to ComfyUI JSON")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if not ENDPOINT_ID or not API_KEY:
        print("ERROR: set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY", file=sys.stderr)
        sys.exit(1)

    try:
        wrapper, root = load_workflow(args.workflow)
        set_prompt(root, args.prompt)
    except Exception as e:
        print(f"ERROR: could not prepare workflow JSON: {e}", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"input": {"workflow": wrapper["input"]["workflow"]}}

    r = requests.post(url, headers=headers, json=payload, timeout=900)
    if r.status_code != 200:
        print(f"HTTP {r.status_code}\n{r.text}", file=sys.stderr)
        sys.exit(1)

    data = r.json()
    try:
        img_b64 = data["output"]["images"][0]["data"]
    except Exception:
        print(f"Bad response:\n{json.dumps(data, ensure_ascii=False, indent=2)}", file=sys.stderr)
        sys.exit(1)

    pathlib.Path(os.path.dirname(args.out) or ".").mkdir(parents=True, exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(base64.b64decode(img_b64))
    print(f"saved -> {args.out}")

if __name__ == "__main__":
    main()
