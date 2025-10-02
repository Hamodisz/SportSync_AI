from __future__ import annotations
import json
from pathlib import Path

# ---- Pillow compatibility shim (pre-import) ----
try:
    from PIL import Image as _PILImage
    if not hasattr(_PILImage, "ANTIALIAS"):
        try:
            _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS
        except Exception:
            pass
except Exception:
    pass

import argparse
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip, vfx
import moviepy.video.fx.resize as mp_resize

# ---- Pillow compatibility shim (moviepy resize) ----
try:
    if getattr(mp_resize, "Image", None) and not hasattr(mp_resize.Image, "ANTIALIAS"):
        from PIL import Image as _PILImage2
        mp_resize.Image.ANTIALIAS = _PILImage2.Resampling.LANCZOS  # type: ignore
except Exception:
    pass

def normalize_path(p: str | Path, repo_root: Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else (repo_root / p).resolve()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True, help="Path to metadata.json")
    ap.add_argument("--out", required=True, help="Output mp4 path")
    args = ap.parse_args()

    meta_path = Path(args.meta).resolve()
    out_path = Path(args.out).resolve()
    repo_root = Path(__file__).resolve().parents[2]

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    images = meta.get("images", [])
    if not images:
        raise ValueError("metadata.json must include a non-empty 'images' array")
    images = [str(normalize_path(p, repo_root)) for p in images]

    secs = meta.get("seconds", 1.2)
    if isinstance(secs, (int, float)):
        durations = [float(secs)] * len(images)
    elif isinstance(secs, list):
        if len(secs) != len(images):
            raise ValueError("'seconds' list must match images length")
        durations = [float(s) for s in secs]
    else:
        raise ValueError("'seconds' must be a number or list")

    fps = int(meta.get("fps", 30))
    texts = meta.get("texts", [])
    if not isinstance(texts, list):
        texts = []
    if len(texts) < len(images):
        texts += [""] * (len(images) - len(texts))

    clips = []
    W, H = 1080, 1920
    for img, dur, txt in zip(images, durations, texts):
        base = (ImageClip(img)
                .resize(height=H)
                .fx(vfx.crop, width=W, height=H)
                .set_duration(dur))
        overlays = [base]
        if txt:
            try:
                cap = (TextClip(txt, fontsize=52, color="white", method="caption", size=(W-80, None))
                       .set_position(("center", H-280)).set_duration(dur))
                shadow = (TextClip(txt, fontsize=52, color="black", method="caption", size=(W-80, None))
                          .set_position(("center", H-276)).set_duration(dur))
                overlays = [base, shadow, cap]
            except Exception:
                overlays = [base]
        clips.append(CompositeVideoClip(overlays).set_duration(dur))

    final = concatenate_videoclips(clips, method="compose")

    audio_path = meta.get("audio")
    if audio_path:
        try:
            apath = str(normalize_path(audio_path, repo_root))
            audio = AudioFileClip(apath)
            if audio.duration > final.duration:
                audio = audio.subclip(0, final.duration)
            final = final.set_audio(audio)
        except Exception:
            pass

    out_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(out_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
        temp_audiofile=str(out_path.parent / "temp-audio.m4a"),
        remove_temp=True,
    )

if __name__ == "__main__":
    main()
