#!/usr/bin/env python3
"""Lightweight TTS dispatcher for Piper / XTTS with a local fallback."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

DEFAULT_DURATION = 6.0
DEFAULT_VOICE = 'en_US-amy-medium'


def which_ffmpeg() -> str:
    helper = Path('tools/which_ffmpeg.sh')
    if helper.exists():
        proc = subprocess.run(['bash', str(helper)], capture_output=True, text=True)
        if proc.returncode == 0:
            candidate = proc.stdout.strip()
            if candidate and candidate != 'FFMPEG_NOT_FOUND':
                return candidate
    return shutil.which('ffmpeg') or 'ffmpeg'


def run_piper(text: str, model: str, output: Path, speaker: str | None) -> bool:
    cli = os.getenv('PIPER_CLI', 'piper')
    cmd = [cli, '-m', model, '-f', str(output)]
    if speaker:
        cmd.extend(['-s', speaker])
    try:
        subprocess.run(cmd, input=text.encode('utf-8'), check=True)
        return output.exists()
    except Exception as exc:  # pragma: no cover - external tool path
        print(f"⚠️ Piper invocation failed: {exc}")
        return False


def run_xtts(text: str, endpoint: str, output: Path, voice: str | None) -> bool:
    payload = {'text': text, 'voice': voice or DEFAULT_VOICE, 'format': 'wav'}
    try:
        import urllib.request

        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            output.write_bytes(resp.read())
        return output.exists()
    except Exception as exc:  # pragma: no cover - network path
        print(f"⚠️ XTTS request failed: {exc}")
        return False


def fallback_tone(text: str, output: Path, duration: float) -> None:
    ffmpeg = which_ffmpeg()
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        '-y',
        '-f',
        'lavfi',
        '-i',
        f'sine=frequency=440:duration={duration}:sample_rate=48000',
        '-af',
        'volume=0.4',
        str(output),
    ]
    subprocess.run(cmd, check=True)
    meta_path = output.with_suffix('.txt')
    meta_path.write_text(text, encoding='utf-8')
    print(f"ℹ️  Placeholder tone generated ({duration}s). Transcript stored at {meta_path}.")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate TTS audio clip for SportSync avatars.')
    parser.add_argument('--text', required=True, help='Narration text')
    parser.add_argument('--voice', default=os.getenv('PIPER_VOICE', DEFAULT_VOICE))
    parser.add_argument('--model', default=os.getenv('PIPER_MODEL'))
    parser.add_argument('--output', required=True, help='Output audio path (wav/mp3)')
    parser.add_argument('--duration', type=float, default=DEFAULT_DURATION)
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.model:
        if run_piper(args.text, args.model, output, args.voice):
            print(f"✅ Piper TTS saved to {output}")
            return 0

    xtts_endpoint = os.getenv('XTTS_ENDPOINT')
    if xtts_endpoint:
        if run_xtts(args.text, xtts_endpoint, output, args.voice):
            print(f"✅ XTTS audio saved to {output}")
            return 0

    fallback_tone(args.text, output, args.duration)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
