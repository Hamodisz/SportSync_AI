#!/usr/bin/env python3
"""Unified entrypoint for SportSync video generation adapters."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from video_pipeline.adapters import get_adapter



def open_video(path: str) -> None:
    from pathlib import Path as _Path
    from platform import system
    from subprocess import CalledProcessError, run

    target = _Path(path)
    if not target.exists():
        print(f"❌ الملف غير موجود: {target}")
        return

    platform_name = system().lower()
    try:
        if platform_name.startswith("darwin"):
            run(["open", str(target)], check=True)
        elif platform_name.startswith("windows"):
            run(["start", str(target)], check=True, shell=True)
        else:
            run(["xdg-open", str(target)], check=True)
    except (CalledProcessError, FileNotFoundError):
        print(f"⚠️ تعذّر فتح الملف تلقائيًا: {target}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SportSync videos using external adapters.")
    parser.add_argument(
        "--mode",
        choices=["shorts", "longform"],
        required=True,
        help="Type of video to generate",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination mp4 path",
    )
    parser.add_argument(
        "--slug",
        help="Identifier used for temporary artifacts (defaults to output stem)",
    )
    parser.add_argument(
        "--language",
        default="ar",
        help="Language code for localisation tweaks",
    )
    parser.add_argument(
        "--headline",
        help="Optional headline override for branding overlays",
    )
    parser.add_argument(
        "--youtube-url",
        help="Source YouTube URL for shorts generation",
    )
    parser.add_argument(
        "--script-file",
        help="Path to a text/JSON file used for longform generation",
    )
    parser.add_argument(
        "--script-json-key",
        help="If --script-file is JSON, pick a field containing the script text",
    )
    parser.add_argument(
        "--script-text",
        help="Raw script text for longform generation (overrides --script-file)",
    )
    return parser.parse_args(argv)


def load_script_text(args: argparse.Namespace) -> str:
    if args.script_text:
        return args.script_text
    if not args.script_file:
        raise ValueError("Either --script-text or --script-file must be provided for longform mode")
    script_path = Path(args.script_file)
    if not script_path.exists():
        raise FileNotFoundError(args.script_file)
    text = script_path.read_text(encoding="utf-8")
    if args.script_json_key:
        payload = json.loads(text)
        key = args.script_json_key
        if key not in payload:
            raise KeyError(f"Key '{key}' not found in {args.script_file}")
        value = payload[key]
        if not isinstance(value, str):
            raise TypeError(f"Value at key '{key}' must be a string, got {type(value)!r}")
        return value
    return text


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    output_path = Path(args.output).resolve()
    slug = args.slug or output_path.stem
    adapter = get_adapter(args.mode)

    if args.mode == "shorts":
        if not args.youtube_url:
            raise ValueError("--youtube-url is required for shorts mode")
        adapter.generate(
            youtube_url=args.youtube_url,
            output_path=output_path,
            slug=slug,
            language=args.language,
            headline=args.headline,
        )
    else:
        script_text = load_script_text(args)
        adapter.generate(
            script_text=script_text,
            script_file=Path(args.script_file) if args.script_file else None,
            output_path=output_path,
            slug=slug,
            language=args.language,
        )

    print(f"✅ Video generated at {output_path}")
    open_video(str(output_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
