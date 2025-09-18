#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
يقص شورتس من فيديو طويل بناءً على markers (JSON أو XML).
يدعم التحويل إلى 9:16 (--vertical).

usage:
  python cut_shorts.py --long ../videos/long/long_001.mp4 --markers ../markers/markers.sample.json --out ../videos/shorts --vertical
  python cut_shorts.py --long ../videos/long/long_001.mp4 --markers ../markers/markers.sample.xml  --out ../videos/shorts

JSON الشكل المتوقع:
{
  "shorts": [
    {"title": "Hook 1", "start": 12.5, "end": 28.0},
    {"title": "Idea 2", "start": 95, "duration": 25}
  ]
}

XML الشكل المتوقع:
<shorts>
  <short title="Hook 1" start="12.5" end="28.0"/>
  <short title="Idea 2" start="95" duration="25"/>
</shorts>
"""

import argparse, json, os, subprocess, pathlib, sys, xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

def load_markers(path: str) -> List[Dict[str, Any]]:
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        return list(data.get("shorts", []))
    elif p.suffix.lower() == ".xml":
        root = ET.fromstring(p.read_text(encoding="utf-8"))
        shorts = []
        for s in root.findall(".//short"):
            item = {
                "title": s.get("title", ""),
                "start": float(s.get("start", "0")),
            }
            if s.get("end") is not None:
                item["end"] = float(s.get("end"))
            if s.get("duration") is not None:
                item["duration"] = float(s.get("duration"))
            shorts.append(item)
        return shorts
    else:
        raise ValueError("markers must be .json or .xml")

def ensure_dir(d: str):
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)

def build_filter(vertical: bool) -> Optional[str]:
    if not vertical:
        return None
    # 9:16 مع حفظ النسبة وتوسيط
    return "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"

def cut_one(long_path: str, out_path: str, start: float, end: Optional[float], dur: Optional[float], vf: Optional[str]):
    ss = max(0.0, float(start))
    if end is not None:
        to = float(end)
        t_opts = ["-to", str(to)]
    elif dur is not None:
        t_opts = ["-t", str(float(dur))]
    else:
        raise ValueError("marker needs 'end' or 'duration'")

    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", long_path]
    if vf:
        cmd += ["-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart"]
    else:
        # دون فلتر = قص سريع مع إعادة ترميز خفيف لضمان التوافق
        cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart"]
    cmd += t_opts
    cmd += [out_path]

    subprocess.run(cmd, check=True)

def sanitize_name(s: str) -> str:
    bad = r' <>:"/\\|?*'
    out = "".join("_" if c in bad else c for c in s)
    return out.strip() or "short"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--long", required=True, help="فيديو طويل (mp4)")
    ap.add_argument("--markers", required=True, help="ملف markers (json/xml)")
    ap.add_argument("--out", required=True, help="مجلد الإخراج")
    ap.add_argument("--vertical", action="store_true", help="حول إلى 9:16 (يوتيوب شورتس)")
    args = ap.parse_args()

    ensure_dir(args.out)
    vf = build_filter(args.vertical)
    shorts = load_markers(args.markers)
    if not shorts:
        print("لا توجد عناصر في markers.", file=sys.stderr)
        sys.exit(1)

    base = pathlib.Path(args.long).stem
    for i, it in enumerate(shorts, start=1):
        title = sanitize_name(it.get("title", f"short_{i}"))
        start = float(it.get("start", 0))
        end = it.get("end")
        dur = it.get("duration")
        out = os.path.join(args.out, f"{base}_{i:02d}_{title}.mp4")
        try:
            cut_one(args.long, out, start, end, dur, vf)
            print(f"[OK] {out}")
        except Exception as e:
            print(f"[ERR] {title}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
