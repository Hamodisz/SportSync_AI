cat > tools/generate_video.py <<'PY'
import os, json, pathlib, subprocess, re, shlex, math
from tools.deepseek_client import chat
from tools.render_scene_image import generate_image

FONT = os.getenv("VIDEO_FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

def ensure_font():
    if not pathlib.Path(FONT).exists():
        # fallback: try another common path
        alt = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if pathlib.Path(alt).exists():
            return alt
    return FONT

def esc_drawtext(s: str) -> str:
    # escape for ffmpeg drawtext (single-quoted)
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    s = re.sub(r"[\r\n]+", " ", s)
    return s

def ff(cmd: list):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{' '.join(cmd)}\n---\n{proc.stdout}")
    return proc.stdout

def build_script(topic: str, vid_type: str):
    n_scenes = 12 if vid_type == "long" else 6
    sys_p = "You write concise video scripts. Output strict JSON with keys: title, scenes[]. Each scene has 'visual' and 'line' (<= 14 words). No markdown."
    user_p = f"""Make a {vid_type} YouTube video script about: "{topic}".
Return JSON only:
{{
  "title": "...",
  "scenes": [
    {{"visual": "what to show", "line": "on-screen caption"}},
    ...
  ]
}}
Constraints:
- scenes length = {n_scenes}
- Avoid banned or sensitive topics.
- Keep 'line' <= 14 words, catchy and positive.
"""
    raw = chat(sys_p, user_p, temperature=0.7, max_tokens=1500)
    m = re.search(r"\{.*\}", raw, re.S)
    data = json.loads(m.group(0)) if m else json.loads(raw)
    data["scenes"] = (data.get("scenes") or [])[:n_scenes]
    assert data["scenes"], "empty scenes"
    return data

def make_scene_clip(img_path: str, line: str, out_mp4: str, width: int, height: int, sec: int, fps: int = 30):
    font = ensure_font()
    fontsize = max(28, int(width * (0.042 if width >= height else 0.055)))
    txt = esc_drawtext(line[:120])
    # Simple scale + caption box at bottom
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=cover,"
        f"format=yuv420p,"
        f"drawtext=fontfile='{font}':text='{txt}':"
        f"fontcolor=white:fontsize={fontsize}:"
        f"box=1:boxcolor=black@0.35:boxborderw=20:"
        f"x=(w-text_w)/2:y=h-(text_h*2)"
    )
    cmd = [
        "ffmpeg","-y","-loop","1","-i",img_path,
        "-t", str(sec), "-r", str(fps),
        "-vf", vf, "-an", "-movflags","+faststart", out_mp4
    ]
    ff(cmd)

def concat_clips(filelist_path: str, out_path: str):
    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",filelist_path,"-c","copy","-movflags","+faststart",out_path]
    ff(cmd)

def generate_video(topic: str, vid_type: str, out_path: str):
    out_path = pathlib.Path(out_path)
    work = out_path.parent / (out_path.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)

    if vid_type == "long":
        width, height, per_sec = 1920, 1080, 50
    else:
        width, height, per_sec = 1080, 1920, 7

    script = build_script(topic, vid_type)
    scenes = script["scenes"]

    img_paths = []
    for idx, sc in enumerate(scenes, start=1):
        prompt = f"{topic}, {sc.get('visual','')}, cinematic, soft light, detailed"
        img_out = work / f"scene_{idx:02d}.png"
        generate_image(prompt, str(img_out), width=width, height=height, seed=123456789 + idx)
        img_paths.append((str(img_out), sc.get("line","").strip() or ""))
    
    # build per-scene clips
    filelist = work / "files.txt"
    with open(filelist, "w", encoding="utf-8") as f:
        for idx, (img, line) in enumerate(img_paths, start=1):
            clip_path = work / f"clip_{idx:02d}.mp4"
            make_scene_clip(img, line, str(clip_path), width, height, per_sec, fps=30)
            f.write(f"file '{clip_path.as_posix()}'\n")

    concat_clips(str(filelist), str(out_path))
    return {"title": script.get("title",""), "out": str(out_path), "scenes": scenes}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True)
    p.add_argument("--type", choices=["long","short"], required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    meta = generate_video(args.topic, args.type, args.out)
    print(json.dumps(meta, ensure_ascii=False))
PY
