#!/usr/bin/env python3
"""Generate subtitle tracks using WhisperX when available with a deterministic fallback."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

DEFAULT_CHUNK_SECONDS = 2.5


def run_whisperx(audio: Path, output: Path, language: str | None) -> bool:
    cli = os.getenv('WHISPERX_CLI')
    if not cli:
        return False

    cmd = [
        cli,
        '--audio',
        str(audio),
        '--output',
        str(output),
        '--format',
        'srt',
    ]
    if language:
        cmd.extend(['--language', language])

    try:
        subprocess.run(cmd, check=True)
        return output.exists()
    except Exception as exc:  # pragma: no cover
        print(f"⚠️ WhisperX failed: {exc}")
        return False


def naive_segments(text: str, chunk: float = DEFAULT_CHUNK_SECONDS) -> list[tuple[float, float, str]]:
    sentences = [t.strip() for t in text.replace('\n', ' ').split('.') if t.strip()]
    timeline: list[tuple[float, float, str]] = []
    cursor = 0.0
    for sentence in sentences:
        duration = max(chunk, len(sentence.split()) * 0.35)
        timeline.append((cursor, cursor + duration, sentence + '.'))
        cursor += duration
    if not timeline:
        timeline.append((0.0, chunk, text.strip() or '...'))
    return timeline


def format_timestamp(value: float) -> str:
    hours = int(value // 3600)
    minutes = int((value % 3600) // 60)
    seconds = int(value % 60)
    millis = int((value - int(value)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def write_srt(timeline: list[tuple[float, float, str]], output: Path) -> None:
    with output.open('w', encoding='utf-8') as handle:
        for idx, (start, end, sentence) in enumerate(timeline, start=1):
            handle.write(f"{idx}\n{format_timestamp(start)} --> {format_timestamp(end)}\n{sentence}\n\n")


def write_ass(timeline: list[tuple[float, float, str]], output: Path) -> None:
    header = """[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: SportSync,DejaVu Sans,46,&H00FFFFFF,&H00FFFFFF,&H00111111,&H80000000,0,0,0,0,100,100,0.6,0,1,3,12,2,80,80,60,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""
    with output.open('w', encoding='utf-8') as handle:
        handle.write(header)
        for start, end, sentence in timeline:
            start_ass = format_timestamp(start).replace(',', '.')
            end_ass = format_timestamp(end).replace(',', '.')
            handle.write(f"Dialogue: 0,{start_ass},{end_ass},SportSync,,0,0,0,,{sentence.replace(',', ';')}\n")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Subtitle generator for SportSync videos.')
    parser.add_argument('--audio', required=True, help='Input audio file (wav/mp3)')
    parser.add_argument('--text', help='Transcript text file (falls back to <audio>.txt if missing)')
    parser.add_argument('--output', required=True, help='Output subtitle path (.srt or .ass)')
    parser.add_argument('--language', help='Language hint for WhisperX')
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    audio = Path(args.audio)
    if not audio.exists():
        raise FileNotFoundError(args.audio)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.suffix.lower() not in {'.srt', '.ass'}:
        raise ValueError('Output must end with .srt or .ass')

    if run_whisperx(audio, output, args.language):
        print(f"✅ WhisperX subtitles written to {output}")
        return 0

    transcript_path = Path(args.text) if args.text else audio.with_suffix('.txt')
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript not found: {transcript_path}")

    text = transcript_path.read_text(encoding='utf-8').strip()
    timeline = naive_segments(text)

    if output.suffix.lower() == '.srt':
        write_srt(timeline, output)
    else:
        write_ass(timeline, output)

    print(f"ℹ️  Generated heuristic subtitles at {output}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
