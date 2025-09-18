#!/usr/bin/env python3
import os, json, argparse, subprocess, xml.etree.ElementTree as ET
from pathlib import Path

def run(cmd):
    print(">>", " ".join(cmd))
    subprocess.check_call(cmd)

def parse_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # توقع: [{"title":"Hook 1","start":"00:00:05.0","end":"00:00:25.0"}]
    return [{"title":i.get("title","short"), "start":i["start"], "end":i["end"]} for i in data]

def parse_xml(path):
    # توقع بسيط:
    # <markers><m title="Hook A" start="00:00:05.0" end="00:00:25.0"/></markers>
    root = ET.parse(path).getroot()
    out = []
    for m in root.findall(".//m"):
        out.append({"title": m.get("title","short"), "start": m.get("start"), "end": m.get("end")})
    return out

def cut_segment(long_path, out_dir, i, seg, vertical=False):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out = os.path.join(out_dir, f"short_{i:02d}.mp4")
    vf = []
    if vertical:
        # نحوّل 16:9 إلى 9:16 (قص+سكيل+باد)
        vf = ["-vf", "scale=1080:-2, crop=1080:1920:(iw-1080)/2:(ih-1920)/2"]
    cmd = [
        "ffmpeg","-y",
        "-ss", seg["start"], "-to", seg["end"],
        "-i", long_path,
        *vf,
        "-c:v","libx264","-preset","veryfast","-c:a","aac","-b:a","128k",
        out
    ]
    run(cmd)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--long", required=True, help="long video path")
    ap.add_argument("--markers", required=True, help="markers .json or .xml")
    ap.add_argument("--out", required=True, help="output dir for shorts")
    ap.add_argument("--vertical", action="store_true", help="export 9:16")
    args = ap.parse_args()

    if args.markers.lower().endswith(".json"):
        segs = parse_json(args.markers)
    else:
        segs = parse_xml(args.markers)

    for i, seg in enumerate(segs, 1):
        cut_segment(args.long, args.out, i, seg, vertical=args.vertical)

    print("Shorts written to", args.out)

if __name__ == "__main__":
    main()
