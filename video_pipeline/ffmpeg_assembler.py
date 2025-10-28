#!/usr/bin/env python3
"""Utility to assemble SportSync teaser videos via FFmpeg.

This script stitches together generated footage, static imagery, music beds,
subtitles, and branding overlays into a final 1080p/30fps deliverable.

Example usage:

python video_pipeline/ffmpeg_assembler.py \
  --slug sportsync_layerz_intro \
  --clips build/generated/segment1.mp4 build/generated/segment2.mp4 \
  --images assets/images/aa_teaser01.png assets/images/ab_teaser02.png \
  --music assets/audio/teaser_pulse.mp3 \
  --subtitles build/captions/layerz.ass

The script is intentionally idempotent: rerunning with the same slug will
rebuild intermediates inside build/tmp/ and replace the final mp4 output.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

BUILD_DIR = Path('build')
TMP_DIR = BUILD_DIR / 'tmp'
DEFAULT_IMAGE_DURATION = 90  # frames at 30fps => 3 seconds
TARGET_FPS = 30
TARGET_SIZE = '1920x1080'


def run_cmd(cmd: Sequence[str], *, quiet: bool = False) -> None:
    """Execute a shell command raising on failure."""
    if not quiet:
        print(' '.join(shlex.quote(part) for part in cmd))
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {' '.join(cmd)}")


def which_ffmpeg() -> str:
    script = Path('tools/which_ffmpeg.sh')
    if script.exists():
        proc = subprocess.run(['bash', str(script)], capture_output=True, text=True)
        candidate = proc.stdout.strip()
        if proc.returncode == 0 and candidate and candidate != 'FFMPEG_NOT_FOUND':
            return candidate
    # Fall back to PATH
    ffmpeg = shutil.which('ffmpeg')  # type: ignore[name-defined]
    if ffmpeg:
        return ffmpeg
    raise RuntimeError('ffmpeg binary not found. Install ffmpeg or place it under vendor/ffmpeg/.')


def ensure_dirs() -> None:
    BUILD_DIR.mkdir(exist_ok=True)
    TMP_DIR.mkdir(exist_ok=True)


def build_image_segment(ffmpeg: str, src: Path, duration_frames: int, index: int) -> Path:
    output = TMP_DIR / f'image_seg_{index:02d}.mp4'
    duration_seconds = duration_frames / TARGET_FPS
    cmd = [
        ffmpeg,
        '-y',
        '-loop',
        '1',
        '-i',
        str(src),
        '-t',
        f'{duration_seconds:.3f}',
        '-vf',
        'zoompan=z=\'min(zoom+0.002,1.07)\':d=60:s=1920x1080,format=yuv420p',
        '-r',
        str(TARGET_FPS),
        str(output),
    ]
    run_cmd(cmd)
    return output


def create_concat_manifest(clips: Iterable[Path]) -> Path:
    manifest = TMP_DIR / 'concat_list.txt'
    with manifest.open('w', encoding='utf-8') as handle:
        for clip in clips:
            handle.write(f"file '{clip.resolve()}'\n")
    return manifest


def concat_clips(ffmpeg: str, manifest: Path, output: Path) -> None:
    cmd = [
        ffmpeg,
        '-y',
        '-f',
        'concat',
        '-safe',
        '0',
        '-i',
        str(manifest),
        '-c',
        'copy',
        str(output),
    ]
    run_cmd(cmd)


def mux_with_audio(
    ffmpeg: str,
    video: Path,
    audio: Path | None,
    subtitles: Path | None,
    output: Path,
) -> None:
    cmd: List[str] = [ffmpeg, '-y', '-i', str(video)]
    if audio:
        cmd.extend(['-i', str(audio)])
    if subtitles and subtitles.suffix.lower() == '.ass':
        cmd.extend(['-filter_complex', f"[0:v]ass={subtitles.resolve()}[v]", '-map', '[v]'])
    else:
        cmd.extend(['-map', '0:v'])

    if audio:
        cmd.extend(['-map', '1:a', '-c:a', 'aac', '-b:a', '128k'])
    else:
        cmd.extend(['-an'])

    cmd.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', str(TARGET_FPS), str(output)])
    run_cmd(cmd)


def assemble(
    slug: str,
    clips: List[Path],
    images: List[Path],
    music: Path | None,
    subtitles: Path | None,
    image_duration_frames: int,
) -> Path:
    ensure_dirs()
    ffmpeg = which_ffmpeg()

    segments: List[Path] = []
    for clip in clips:
        segments.append(clip)

    for index, image in enumerate(images):
        segments.append(build_image_segment(ffmpeg, image, image_duration_frames, index))

    if not segments:
        raise RuntimeError('No clips or images provided for assembly.')

    concat_video = TMP_DIR / f'{slug}_concat.mp4'
    manifest = create_concat_manifest(segments)
    concat_clips(ffmpeg, manifest, concat_video)

    final_output = BUILD_DIR / f'{slug}.mp4'
    mux_with_audio(ffmpeg, concat_video, music, subtitles, final_output)
    return final_output


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Assemble final SportSync video via FFmpeg.')
    parser.add_argument('--slug', required=True, help='Slug used for build/<slug>.mp4 output')
    parser.add_argument('--clips', nargs='*', default=[], help='Pre-rendered video segments to concatenate')
    parser.add_argument('--images', nargs='*', default=[], help='Images to animate into short clips')
    parser.add_argument('--music', help='Optional background music track (mp3/wav)')
    parser.add_argument('--subtitles', help='Optional subtitles file (.ass preferred)')
    parser.add_argument('--image-duration', type=int, default=DEFAULT_IMAGE_DURATION,
                        help='Duration per image expressed in frames (default 90 = 3 seconds)')
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)

    clips = [Path(p) for p in args.clips]
    images = [Path(p) for p in args.images]
    music = Path(args.music) if args.music else None
    subtitles = Path(args.subtitles) if args.subtitles else None

    output = assemble(args.slug, clips, images, music, subtitles, args.image_duration)
    print(f'✅ Assembled video: {output.resolve()}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
