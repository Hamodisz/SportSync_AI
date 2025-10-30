from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_ROOT = PROJECT_ROOT / "external"
BRAND_DIR = PROJECT_ROOT / "assets" / "brand"
DEFAULT_BRAND_COLORS = {
    "background": "#0d1628",
    "accent": "#5dd0ff",
}
LOGGER = logging.getLogger(__name__)


def resolve_external(*parts: str) -> Path:
    path = EXTERNAL_ROOT.joinpath(*parts)
    if not path.exists():
        raise FileNotFoundError(f"Expected external asset missing: {path}")
    return path


def which_ffmpeg() -> str:
    helper = PROJECT_ROOT / "tools" / "which_ffmpeg.sh"
    if helper.exists():
        proc = subprocess.run(["bash", str(helper)], capture_output=True, text=True, check=False)
        candidate = proc.stdout.strip()
        if proc.returncode == 0 and candidate and candidate != "FFMPEG_NOT_FOUND":
            return candidate
    env_ffmpeg = os.getenv("FFMPEG")
    if env_ffmpeg:
        return env_ffmpeg
    path_ffmpeg = shutil.which("ffmpeg")
    if path_ffmpeg:
        return path_ffmpeg
    raise RuntimeError("ffmpeg binary is required for video generation")


def ensure_output_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_ffmpeg(args: Sequence[str]) -> None:
    ffmpeg = which_ffmpeg()
    cmd = [ffmpeg, *args]
    LOGGER.debug("Running ffmpeg command: %s", " ".join(cmd))
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg failed with exit code {completed.returncode}")


def brand_logo() -> Path:
    logo_path = BRAND_DIR / "logo.png"
    if not logo_path.exists():
        raise FileNotFoundError(f"Brand logo missing at {logo_path}")
    return logo_path


def default_font() -> Path:
    candidates = [
        PROJECT_ROOT / "vendor" / "fonts" / "DejaVuSans.ttf",
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Unable to locate a fallback font for ffmpeg drawtext")


def sanitize_drawtext(text: str) -> str:
    sanitized = text.replace("\\", "\\\\")
    sanitized = sanitized.replace(":", r"\:")
    sanitized = sanitized.replace("\n", r"\n")
    sanitized = sanitized.replace("'", r"\'")
    return sanitized


def generate_placeholder_video(
    output_path: Path,
    *,
    headline: str,
    subtitle: str,
    duration: int = 10,
) -> Path:
    ensure_output_path(output_path)
    font_path = default_font()
    ffmpeg_args = [
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={DEFAULT_BRAND_COLORS['background']}:s=1920x1080:d={duration}",
        "-i",
        str(brand_logo()),
        "-filter_complex",
        (
            "[1:v]scale=-1:420:force_original_aspect_ratio=decrease,format=rgba[logo];"
            "[0:v][logo]overlay=(W-w)/2:240:format=auto,format=yuv420p[with_logo];"
            f"[with_logo]drawtext=fontfile='{font_path}':"
            f"text='{sanitize_drawtext(headline)}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=760,"
            f"drawtext=fontfile='{font_path}':"
            f"text='{sanitize_drawtext(subtitle)}':fontcolor={DEFAULT_BRAND_COLORS['accent']}:fontsize=42:x=(w-text_w)/2:y=860"
        ),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]
    run_ffmpeg(ffmpeg_args)
    return output_path


def apply_brand_overlay(
    source_video: Path,
    output_path: Path,
    *,
    headline: str,
    subtitle: str,
) -> Path:
    ensure_output_path(output_path)
    font_path = default_font()
    ffmpeg_args = [
        "-y",
        "-i",
        str(source_video),
        "-i",
        str(brand_logo()),
        "-filter_complex",
        (
            "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=rgba[base];"
            "[1:v]scale=-1:300:force_original_aspect_ratio=decrease,format=rgba[logo];"
            "[base][logo]overlay=80:60:format=auto,format=yuv420p[with_logo];"
            f"[with_logo]drawtext=fontfile='{font_path}':"
            f"text='{sanitize_drawtext(headline)}':fontcolor=white:fontsize=64:x=120:y=840,"
            f"drawtext=fontfile='{font_path}':"
            f"text='{sanitize_drawtext(subtitle)}':fontcolor={DEFAULT_BRAND_COLORS['accent']}:fontsize=42:x=120:y=920"
        ),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        str(output_path),
    ]
    run_ffmpeg(ffmpeg_args)
    return output_path
