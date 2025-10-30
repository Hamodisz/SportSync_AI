#!/usr/bin/env python3
"""Request short motion clips from a ComfyUI (AnimateDiff / SVD) endpoint.

The script reads a JSON prompt describing the desired look & feel. When a
COMFYUI_ENDPOINT environment variable is defined it will attempt to trigger the
remote workflow. If the endpoint is missing (local development without GPU), it
falls back to generating a branded still frame that can be animated later via
Ken Burns.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict
from urllib import request

BUILD_DIR = Path('build/generated')


def which_ffmpeg() -> str:
    helper = Path('tools/which_ffmpeg.sh')
    if helper.exists():
        proc = subprocess.run(['bash', str(helper)], capture_output=True, text=True)
        if proc.returncode == 0:
            candidate = proc.stdout.strip()
            if candidate and candidate != 'FFMPEG_NOT_FOUND':
                return candidate
    return shutil.which('ffmpeg') or 'ffmpeg'


def comfy_request(endpoint: str, payload: Dict[str, Any]) -> bytes:
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(endpoint, data=data, headers={'Content-Type': 'application/json'})
    with request.urlopen(req, timeout=120) as resp:
        return resp.read()


def fallback_frame(prompt: Dict[str, Any], output: Path) -> Path:
    ffmpeg = which_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)
    title = prompt.get('title') or 'SportSync Layer-Z'
    style = prompt.get('style') or 'Concept Vision'
    color = prompt.get('palette', {}).get('background', '#101b2e')
    accent = prompt.get('palette', {}).get('accent', '#5dd0ff')

    cmd = [
        ffmpeg,
        '-y',
        '-f',
        'lavfi',
        '-i',
        f"color=c={color}:s=1920x1080",
        '-vf',
        (
            "drawbox=x=0:y=0:w=1920:h=1080:color=#000000@0.55:t=fill,"\
            "drawtext=fontfile=vendor/fonts/DejaVuSans.ttf:text='" + title.replace("'", "") + "':"
            "fontcolor=white:fontsize=72:x=(w-text_w)/2:y=420,"\
            "drawtext=fontfile=vendor/fonts/DejaVuSans.ttf:text='" + style.replace("'", "") + " vibes':"
            f"fontcolor={accent}:fontsize=48:x=(w-text_w)/2:y=520"
        ),
        '-frames:v',
        '1',
        '-update',
        '1',
        str(output),
    ]
    subprocess.run(cmd, check=True)
    return output


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description='Generate a stylised motion clip via ComfyUI.')
    parser.add_argument('prompt_json', help='Path to a JSON file describing the prompt/styling.')
    parser.add_argument('--slug', default='clip', help='Name for the generated asset placed under build/generated/')
    args = parser.parse_args(argv)

    prompt_path = Path(args.prompt_json)
    if not prompt_path.exists():
        raise FileNotFoundError(args.prompt_json)

    payload = json.loads(prompt_path.read_text(encoding='utf-8'))
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output_video = BUILD_DIR / f"{args.slug}.mp4"

    endpoint = os.getenv('COMFYUI_ENDPOINT')
    if endpoint:
        try:
            print(f"🔌 Hitting ComfyUI endpoint: {endpoint}")
            response = comfy_request(endpoint, payload)
            tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            tmp.write(response)
            tmp.close()
            final_cmd = [
                which_ffmpeg(),
                '-y',
                '-i',
                tmp.name,
                '-vf',
                'scale=1920:1080:force_original_aspect_ratio=decrease,format=yuv420p',
                '-r',
                '30',
                str(output_video),
            ]
            subprocess.run(final_cmd, check=True)
            print(f"✅ Generated motion clip: {output_video}")
            return 0
        except Exception as exc:  # pragma: no cover - network path
            print(f"⚠️  ComfyUI request failed, falling back to static frame. ({exc})")

    fallback_frame(payload, output_video.with_suffix('.png'))
    print(f"ℹ️ Fallback image created at {output_video.with_suffix('.png')}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
