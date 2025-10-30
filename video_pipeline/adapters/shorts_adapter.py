from __future__ import annotations

import contextlib
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, List, Tuple

from .helpers import (
    apply_brand_overlay,
    ensure_output_path,
    generate_placeholder_video,
    resolve_external,
)

LOGGER = logging.getLogger(__name__)


class ShortsAdapter:
    """Bridge the AI-Youtube-Shorts-Generator project into SportSync."""

    def __init__(self) -> None:
        self.repo_root = resolve_external("AI-Youtube-Shorts-Generator")

    def generate(
        self,
        *,
        youtube_url: str,
        output_path: Path,
        slug: str,
        language: str = "ar",
        headline: str | None = None,
    ) -> Path:
        if not youtube_url:
            raise ValueError("youtube_url is required for shorts generation")
        ensure_output_path(output_path)
        headline_text, subtitle_text = self._localized_copy(language, headline)
        try:
            final_video = self._generate_core(
                youtube_url=youtube_url,
                output_path=output_path,
                slug=slug,
                headline=headline_text,
                subtitle=subtitle_text,
            )
            LOGGER.info("Short-form video generated at %s", final_video)
            return final_video
        except Exception as exc:  # pragma: no cover - heavy deps
            LOGGER.warning("Shorts adapter failed (%s). Falling back to placeholder.", exc)
            return generate_placeholder_video(
                output_path,
                headline=headline_text,
                subtitle=subtitle_text,
            )

    def _generate_core(
        self,
        *,
        youtube_url: str,
        output_path: Path,
        slug: str,
        headline: str,
        subtitle: str,
    ) -> Path:
        with self._external_modules():
            from Components.Edit import crop_video  # type: ignore

            extractor = self._resolve_extractor()
            highlight_finder = self._resolve_highlight_finder()
            transcript_fn = self._resolve_transcriber()

            with tempfile.TemporaryDirectory(prefix="sportsync_shorts_") as tmp:
                tmp_dir = Path(tmp)
                source_video = extractor(youtube_url, tmp_dir)
                if source_video is None:
                    raise RuntimeError("Video download failed")

                duration = self._get_video_duration(source_video)
                start, end = self._pick_highlight(
                    transcript_fn,
                    highlight_finder,
                    source_video,
                    duration,
                )
                trimmed = tmp_dir / f"{slug}_trimmed.mp4"
                crop_video(str(source_video), str(trimmed), start, end)

                vertical = self._verticalize(trimmed, tmp_dir)
                branded_output = tmp_dir / f"{slug}_branded.mp4"
                apply_brand_overlay(
                    vertical,
                    branded_output,
                    headline=headline,
                    subtitle=subtitle,
                )
                shutil.copy2(branded_output, output_path)
                return output_path

    def _resolve_extractor(self):
        def download(youtube_url: str, workdir: Path) -> Path | None:
            try:
                from pytubefix import YouTube  # type: ignore
            except Exception as exc:
                raise RuntimeError("pytubefix is required for shorts generation") from exc

            yt = YouTube(youtube_url)
            stream = (
                yt.streams.filter(progressive=True, file_extension="mp4")
                .order_by("resolution")
                .desc()
                .first()
            )
            if stream is None:
                stream = (
                    yt.streams.filter(type="video", file_extension="mp4")
                    .order_by("resolution")
                    .desc()
                    .first()
                )
            if stream is None:
                raise RuntimeError("No downloadable streams discovered")
            file_path = Path(stream.download(output_path=str(workdir), filename=f"{yt.video_id}.mp4"))
            LOGGER.info("Downloaded YouTube video to %s", file_path)
            return file_path

        return download

    def _resolve_transcriber(self):
        with contextlib.suppress(Exception):
            from Components.Transcription import transcribeAudio  # type: ignore

            return transcribeAudio
        return None

    def _resolve_highlight_finder(self):
        if "OPENAI_API" not in os.environ and os.getenv("OPENAI_API_KEY"):
            os.environ.setdefault("OPENAI_API", os.environ["OPENAI_API_KEY"])
        with contextlib.suppress(Exception):
            from Components.LanguageTasks import GetHighlight  # type: ignore

            return GetHighlight
        return None

    @contextlib.contextmanager
    def _external_modules(self):
        sys.path.insert(0, str(self.repo_root))
        try:
            yield
        finally:
            with contextlib.suppress(ValueError):
                sys.path.remove(str(self.repo_root))

    def _localized_copy(self, language: str, headline: str | None) -> Tuple[str, str]:
        lang = (language or "").lower()
        if lang in {"ar", "العربية", "arabic"}:
            return (
                headline or "فيديو قصير من SportSync",
                "نجهز أفضل القصص الرياضية لك الآن",
            )
        return (
            headline or "SportSync Shorts Preview",
            "Polishing your highlight reel...",
        )

    def _get_video_duration(self, video_path: Path) -> float:
        from moviepy.editor import VideoFileClip  # type: ignore

        with VideoFileClip(str(video_path)) as clip:
            return float(clip.duration)

    def _pick_highlight(
        self,
        transcript_fn,
        highlight_finder,
        source_video: Path,
        fallback_duration: float,
    ) -> Tuple[int, int]:
        if transcript_fn is None or highlight_finder is None:
            return 0, min(int(fallback_duration), 60)

        from Components.Edit import extractAudio  # type: ignore

        audio_path = extractAudio(str(source_video))
        if not audio_path:
            return 0, min(int(fallback_duration), 60)
        transcripts = transcript_fn(audio_path) or []
        if not transcripts:
            return 0, min(int(fallback_duration), 60)
        transcription_payload = self._compose_transcription(transcripts)
        start, end = highlight_finder(transcription_payload)
        if end <= start:
            end = min(start + 60, int(fallback_duration))
        return int(start), int(end)

    def _compose_transcription(self, segments: Iterable[Iterable[Any]]) -> str:
        lines: List[str] = []
        for segment in segments:
            try:
                text, start, end = segment
            except ValueError:
                continue
            lines.append(f"{start:.2f} - {end:.2f}: {text}")
        return "\n".join(lines)

    def _verticalize(self, video_path: Path, workdir: Path) -> Path:
        from moviepy.editor import VideoFileClip  # type: ignore

        vertical_path = workdir / f"{video_path.stem}_vertical.mp4"
        with VideoFileClip(str(video_path)) as clip:
            target_aspect = 9 / 16
            current_aspect = clip.w / clip.h
            if current_aspect > target_aspect:
                new_width = int(clip.h * target_aspect)
                x_center = clip.w / 2
                x1 = int(x_center - new_width / 2)
                x2 = int(x_center + new_width / 2)
                cropped = clip.crop(x1=x1, x2=x2)
            else:
                cropped = clip
            resized = cropped.resize(height=1080)
            resized.write_videofile(
                str(vertical_path),
                codec="libx264",
                audio_codec="aac",
                fps=min(int(clip.fps or 30), 60),
                verbose=False,
                logger=None,
            )
        return vertical_path
