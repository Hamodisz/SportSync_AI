#!/usr/bin/env python3
"""Wrapper around LivePortrait / SadTalker pipelines with graceful fallback."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def which_ffmpeg() -> str:
    helper = Path('tools/which_ffmpeg.sh')
    if helper.exists():
        proc = subprocess.run(['bash', str(helper)], capture_output=True, text=True)
        if proc.returncode == 0:
            candidate = proc.stdout.strip()
            if candidate and candidate != 'FFMPEG_NOT_FOUND':
                return candidate
    return shutil.which('ffmpeg') or 'ffmpeg'


def liveportrait_cli() -> str | None:
    return os.getenv('LIVEPORTRAIT_CLI') or os.getenv('SADTALKER_CLI')


def run_liveportrait(cli: str, image: Path, audio: Path, output: Path) -> bool:
    cmd = [cli, '--image', str(image), '--audio', str(audio), '--output', str(output)]
    try:
        print(' '.join(cmd))
        subprocess.run(cmd, check=True)
        return output.exists()
    except Exception as exc:  # pragma: no cover - external binary path
        print(f"⚠️  LivePortrait run failed: {exc}")
        return False


def fallback_render(image: Path, audio: Path | None, output: Path, duration: float) -> None:
    ffmpeg = which_ffmpeg()
    cmd: list[str] = [
        ffmpeg,
        '-y',
        '-loop',
        '1',
        '-i',
        str(image),
    ]
    extra_flags = []
    if audio and audio.exists():
        cmd.extend(['-i', str(audio)])
        extra_flags.extend(['-c:a', 'aac', '-b:a', '128k', '-shortest'])
    else:
        cmd.extend(['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono'])
        extra_flags.append('-shortest')

    cmd.extend([
        '-t', f'{duration:.2f}',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-tune', 'stillimage',
        '-pix_fmt', 'yuv420p',
        '-r', '30',
        *extra_flags,
        str(output),
    ])
    subprocess.run(cmd, check=True)
    print(f"ℹ️  Fallback talking-head (static) written to {output}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate SportSync virtual coach talking-head clip.')
    parser.add_argument('--image', required=True, help='Driving portrait image (PNG/JPG)')
    parser.add_argument('--audio', help='Voice-over audio (wav/mp3)')
    parser.add_argument('--output', required=True, help='Output mp4 path')
    parser.add_argument('--duration', type=float, default=10.0, help='Target duration when audio is missing (seconds)')
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    image = Path(args.image)
    if not image.exists():
        raise FileNotFoundError(args.image)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    audio = Path(args.audio) if args.audio else None

    cli = liveportrait_cli()
    if cli and audio:
        if run_liveportrait(cli, image, audio, output):
            print(f"✅ LivePortrait output: {output}")
            return 0

    print('ℹ️  Falling back to still-image video composition.')
    fallback_render(image, audio, output, args.duration)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
