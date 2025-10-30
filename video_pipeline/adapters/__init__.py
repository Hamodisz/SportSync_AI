"""Adapter layer unifying external video generators with SportSync branding."""

from __future__ import annotations

from .longform_adapter import LongformAdapter
from .shorts_adapter import ShortsAdapter

__all__ = ["ShortsAdapter", "LongformAdapter"]


def get_adapter(kind: str) -> ShortsAdapter | LongformAdapter:
    """Return an adapter instance for the requested video kind."""
    normalized = (kind or "").strip().lower()
    if normalized in {"short", "shorts"}:
        return ShortsAdapter()
    if normalized in {"long", "longform", "full"}:
        return LongformAdapter()
    raise ValueError(f"Unsupported adapter kind: {kind!r}")
