#!/usr/bin/env python3
"""End-to-end helper that turns a Layer-Z formatted payload into a teaser video."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
REMOTION_PAYLOAD = ROOT / 'content_studio/remotion/payload/latest.json'


def run(cmd: List[str], *, cwd: Path | None = None) -> None:
    print('▶', ' '.join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)


def ensure_build() -> None:
    (BUILD / 'generated').mkdir(parents=True, exist_ok=True)
    (ROOT / 'publishers/youtube/pending').mkdir(parents=True, exist_ok=True)


def load_config(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'title' not in data:
        raise ValueError('config must include a "title" field')
    data.setdefault('slug', data['title'].lower().replace(' ', '_'))
    data.setdefault('bullets', [])
    data.setdefault('script', 'Welcome to SportSync Layer-Z insights!')
    data.setdefault('images', [])
    data.setdefault('prompts', [])
    data.setdefault('brandSignature', {
        'palette': {
            'background': '#0d1628',
            'accent': '#5dd0ff',
            'text': '#ffffff'
        },
        'logo': 'assets/brand/logo.png',
        'tagline': 'Layer-Z Intelligence by SportSync'
    })
    return data


def generate_tts(slug: str, text: str, voice: str | None) -> Path:
    audio_path = BUILD / f'{slug}_voice.wav'
    cmd = [
        sys.executable,
        str(ROOT / 'ai_avatars/tts/tts.py'),
        '--text',
        text,
        '--output',
        str(audio_path),
    ]
    if voice:
        cmd.extend(['--voice', voice])
    run(cmd)
    transcript_path = audio_path.with_suffix('.txt')
    transcript_path.write_text(text, encoding='utf-8')
    return audio_path


def generate_subtitles(slug: str, audio_path: Path) -> Dict[str, Path]:
    srt_path = BUILD / f'{slug}.srt'
    ass_path = BUILD / f'{slug}.ass'
    transcript_path = audio_path.with_suffix('.txt')
    run([
        sys.executable,
        str(ROOT / 'ai_avatars/whisper/subs.py'),
        '--audio',
        str(audio_path),
        '--text',
        str(transcript_path),
        '--output',
        str(srt_path),
    ])
    # Generate ASS variant for styling
    run([
        sys.executable,
        str(ROOT / 'ai_avatars/whisper/subs.py'),
        '--audio',
        str(audio_path),
        '--text',
        str(transcript_path),
        '--output',
        str(ass_path),
    ])
    return {'srt': srt_path, 'ass': ass_path}


def maybe_generate_clips(config: Dict[str, Any]) -> List[Path]:
    output_clips: List[Path] = []
    for index, prompt_file in enumerate(config.get('prompts', [])):
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            print(f"⚠️ Prompt not found: {prompt_path}, skipping")
            continue
        slug = f"{config['slug']}_clip{index+1}"
        run([
            sys.executable,
            str(ROOT / 'video_pipeline/comfyui/generate_clip.py'),
            str(prompt_path),
            '--slug',
            slug,
        ])
        mp4_path = BUILD / 'generated' / f'{slug}.mp4'
        png_path = mp4_path.with_suffix('.png')
        if mp4_path.exists():
            output_clips.append(mp4_path)
        elif png_path.exists():
            output_clips.append(png_path)
    return output_clips


def assemble_video(config: Dict[str, Any], clips: List[Path], subtitles: Dict[str, Path]) -> Path:
    slug = config['slug']
    images = [Path(p) for p in config.get('images', [])]
    images.extend(clips)
    music = config.get('music') or 'assets/audio/teaser_pulse.mp3'
    music_path = Path(music)
    assembler_cmd = [
        sys.executable,
        str(ROOT / 'video_pipeline/ffmpeg_assembler.py'),
        '--slug',
        slug,
        '--image-duration',
        '90',
    ]
    video_clips = [p for p in images if p.suffix.lower() == '.mp4']
    stills = [p for p in images if p.suffix.lower() != '.mp4']
    if video_clips:
        assembler_cmd.extend(['--clips', *map(str, video_clips)])
    if stills:
        assembler_cmd.extend(['--images', *map(str, stills)])
    if music_path.exists():
        assembler_cmd.extend(['--music', str(music_path)])
    if subtitles.get('ass') and subtitles['ass'].exists():
        assembler_cmd.extend(['--subtitles', str(subtitles['ass'])])
    run(assembler_cmd)
    return BUILD / f"{slug}.mp4"


def update_remotion_payload(config: Dict[str, Any], clips: List[Path]) -> None:
    REMOTION_PAYLOAD.parent.mkdir(parents=True, exist_ok=True)
    footage = []
    for clip in clips:
        footage.append({
            'type': 'video' if clip.suffix.lower() == '.mp4' else 'image',
            'src': str(clip),
        })
    payload = {
        'title': config['title'],
        'bullets': config.get('bullets', []),
        'footage': footage,
        'brandSignature': config.get('brandSignature'),
    }
    REMOTION_PAYLOAD.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Drive the SportSync video creation pipeline.')
    parser.add_argument('--config', required=True, help='JSON config containing title, bullets, script, etc.')
    parser.add_argument('--voice', help='Voice id for the TTS backend (Piper / XTTS).')
    parser.add_argument('--render-remotion', action='store_true', help='Render the Remotion short teaser alongside the FFmpeg output.')
    parser.add_argument('--upload', action='store_true', help='Attempt automatic YouTube upload after render.')
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(args.config)
    config = load_config(config_path)

    ensure_build()
    audio_path = generate_tts(config['slug'], config['script'], args.voice)
    subtitles = generate_subtitles(config['slug'], audio_path)
    clips = maybe_generate_clips(config)
    final_path = assemble_video(config, clips, subtitles)

    update_remotion_payload(config, clips)

    if args.render_remotion:
        remotion_dir = ROOT / 'content_studio/remotion'
        run(['npm', 'run', 'render', '--', 'short-teaser', str(final_path.with_name(f"{config['slug']}_remotion.mp4"))], cwd=remotion_dir)

    if args.upload:
        run([
            sys.executable,
            str(ROOT / 'publishers/youtube/upload.py'),
            '--file',
            str(final_path),
            '--title',
            config['title'],
            '--desc',
            config.get('description', 'SportSync Layer-Z teaser'),
            '--tags',
            ','.join(config.get('tags', ['SportSync', 'LayerZ', 'Teaser'])),
        ])

    print(f"🎬 Video ready at {final_path.resolve()}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
