from __future__ import annotations

import contextlib
import logging
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import List

from .helpers import (
    DEFAULT_BRAND_COLORS,
    brand_logo,
    default_font,
    ensure_output_path,
    generate_placeholder_video,
    resolve_external,
    run_ffmpeg,
    sanitize_drawtext,
)

LOGGER = logging.getLogger(__name__)


class LongformAdapter:
    """Wrapper around the text2youtube project for SportSync long-form videos."""

    def __init__(self) -> None:
        self.repo_root = resolve_external("text2youtube")

    def generate(
        self,
        *,
        script_text: str | None,
        script_file: Path | None,
        output_path: Path,
        slug: str,
        language: str = "ar",
    ) -> Path:
        if not script_text and not script_file:
            raise ValueError("Either script_text or script_file must be provided")
        text = script_text or script_file.read_text(encoding="utf-8")
        ensure_output_path(output_path)
        headline, subtitle = self._localized_copy(language)
        try:
            data = self._parse_script(text)
            return self._render_story(slug, data, output_path)
        except Exception as exc:  # pragma: no cover - integration path
            LOGGER.warning("Longform adapter failed (%s). Using placeholder.", exc)
            preview = subtitle if subtitle else "SportSync long-form story"
            return generate_placeholder_video(output_path, headline=headline, subtitle=preview)

    def _parse_script(self, raw_text: str) -> dict:
        with self._external_repo():
            from src.utils import split_openai_output  # type: ignore

            try:
                elements = split_openai_output(raw_text)
            except Exception as exc:  # type: ignore[broad-except]
                LOGGER.warning("split_openai_output failed (%s); falling back to naive parsing", exc)
                return {
                    "title": "SportSync Narrative",
                    "description": raw_text.strip().splitlines()[0] if raw_text.strip() else "",
                    "sections": [segment for segment in raw_text.split("\\n\\n") if segment.strip()],
                }

        title = next((item.text for item in elements if item.type == "title"), "SportSync Narrative")
        description = next((item.text for item in elements if item.type == "description"), "")
        sections = [item.text for item in elements if item.type == "text"]
        if not sections:
            sections = [segment for segment in raw_text.split("\\n\\n") if segment.strip()]
        return {
            "title": title.strip() or "SportSync Narrative",
            "description": description.strip(),
            "sections": sections[:6],
        }

    def _render_story(self, slug: str, data: dict, output_path: Path) -> Path:
        sections: List[str] = data.get("sections", []) or [data.get("description", "")]
        headline = data.get("title", "SportSync Narrative")
        with tempfile.TemporaryDirectory(prefix="sportsync_longform_") as tmp:
            tmp_dir = Path(tmp)
            segment_paths: List[Path] = []
            for index, text in enumerate(sections, start=1):
                segment_paths.append(self._render_segment(tmp_dir, slug, index, text, headline))
            final_video = tmp_dir / f"{slug}_longform.mp4"
            if len(segment_paths) == 1:
                final_video.write_bytes(segment_paths[0].read_bytes())
            else:
                concat_list = tmp_dir / "concat.txt"
                concat_list.write_text("\n".join(f"file '{path}'" for path in segment_paths), encoding="utf-8")
                run_ffmpeg([
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_list),
                    "-c",
                    "copy",
                    str(final_video),
                ])
            output_path.write_bytes(final_video.read_bytes())
            return output_path

    def _render_segment(self, tmp_dir: Path, slug: str, index: int, text: str, headline: str) -> Path:
        wrapped = textwrap.fill(text.strip(), width=42)
        segment_path = tmp_dir / f"{slug}_segment_{index:02d}.mp4"
        logo_path = brand_logo()
        font_path = self._font_path()
        overlay_text = sanitize_drawtext(wrapped)
        overlay_headline = sanitize_drawtext(headline)
        filter_complex = (
            "[1:v]scale=-1:260:force_original_aspect_ratio=decrease,format=rgba[logo];"
            "[0:v][logo]overlay=80:80:format=auto,format=yuv420p[base];"
            f"[base]drawtext=fontfile='{font_path}':text='{overlay_headline}':"
            "fontcolor=white:fontsize=56:x=120:y=750,"
            f"drawtext=fontfile='{font_path}':text='{overlay_text}':"
            "fontcolor=white:fontsize=42:x=120:y=860:line_spacing=12"
        )
        run_ffmpeg([
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={DEFAULT_BRAND_COLORS['background']}:s=1920x1080:d=10",
            "-i",
            str(logo_path),
            "-filter_complex",
            ''.join(filter_complex),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(segment_path),
        ])
        return segment_path

    def _localized_copy(self, language: str) -> tuple[str, str]:
        lang = (language or "").lower()
        if lang in {"ar", "العربية", "arabic"}:
            return "قصة SportSync الكاملة", "سنكشف تفاصيل التجربة قريبًا"
        return "SportSync Full Story", "Crafting your long-form narrative"

    def _font_path(self) -> Path:
        return default_font()

    @contextlib.contextmanager
    def _external_repo(self):
        sys.path.insert(0, str(self.repo_root))
        try:
            yield
        finally:
            with contextlib.suppress(ValueError):
                sys.path.remove(str(self.repo_root))
