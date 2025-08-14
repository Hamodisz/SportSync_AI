#!/usr/bin/env python3
"""Simple smoke test for stock image fetching."""
from pathlib import Path
from content_studio.ai_images.generate_images import generate_images

SCRIPT = (
    "Scene 1: A bright stadium\n\n"
    "Scene 2: A cheering crowd\n\n"
    "Scene 3: A trophy lift"
)

if __name__ == "__main__":
    paths = generate_images(SCRIPT, "en", use_stock=True, use_openai=False)
    print(paths)
    existing = [p for p in paths if Path(p).exists()]
    raise SystemExit(0 if existing else 1)
