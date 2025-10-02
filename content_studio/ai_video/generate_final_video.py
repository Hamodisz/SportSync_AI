# --- Pillow compatibility shim (pre-import) ---
from PIL import Image as _PILImage
if not hasattr(_PILImage, "ANTIALIAS"):
    try:
        _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS
    except Exception:
        pass
# ----------------------------------------------

import json
import argparse
from pathlib import Path

# استيراد MoviePy
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, TextClip, vfx
from moviepy.audio.AudioClip import concatenate_audioclips

# --- Pillow compatibility shim (post-import: patch module used داخل resize) ---
try:
    import moviepy.video.fx.resize as _mp_resize
    # _mp_resize.Image هو نفس كائن PIL.Image داخل الموديول
    if hasattr(_PILImage, "Resampling") and not hasattr(_mp_resize.Image, "ANTIALIAS"):
        _mp_resize.Image.ANTIALIAS = _PILImage.Resampling.LANCZOS
except Exception:
    pass
# ------------------------------------------------------------------------------

def normalize_path(p: str, repo_root: Path) -> Path:
    pp = Path(p)
    if pp.is_absolute():
        return pp
    if str(pp).startswith("../"):
        return (repo_root / str(pp)[3:]).resolve()
    return (repo_root / pp).resolve()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True, help="Path to metadata.json")
    ap.add_argument("--out", required=True, help="Output mp4 path")
    args = ap.parse_args()

    meta_path = Path(args.meta).resolve()
    out_path = Path(args.out).resolve()
    repo_root = Path(__file__).resolve().parents[2]

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    seconds = float(meta.get("seconds", 1.2))
    fps = int(meta.get("fps", 30))
    images = meta.get("images", [])
    title = meta.get("title", "")
    subtitle = meta.get("subtitle", "")
    anim = meta.get("animation", {}) or {}
    crossfade = float(anim.get("crossfade", 0.25))
    colorx = float(anim.get("colorx", 1.0))

    if not images:
        raise SystemExit("No images listed in metadata.json")

    clips = []
    for p in images:
        full = normalize_path(p, repo_root)
        if not full.exists():
            raise SystemExit(f"Image not found: {full}")
        c = ImageClip(str(full)).set_duration(seconds).resize(height=1920)
        if c.w < 1080:
            c = c.resize(width=1080)
        if colorx != 1.0:
            c = c.fx(vfx.colorx, colorx)
        clips.append(c)

    # crossfade assemble
    xclips = []
    for i, c in enumerate(clips):
        if i == 0:
            xclips.append(c)
        else:
            xclips.append(c.crossfadein(crossfade))
            xclips[i-1] = xclips[i-1].crossfadeout(crossfade)

    video = concatenate_videoclips(xclips, method="compose")

    # simple title/subtitle overlay (اختياري)
    try:
        overlays = [video]
        if title:
            t = TextClip(title, fontsize=64, color='white').set_duration(min(4, seconds*2)).set_position(("center", 200)).fadein(0.4).fadeout(0.4)
            overlays.append(t)
        if subtitle:
            s = TextClip(subtitle, fontsize=30, color='white').set_duration(min(4, seconds*2)).set_position(("center", 1720)).fadein(0.4).fadeout(0.4)
            overlays.append(s)
        video = CompositeVideoClip(overlays, size=(1080,1920)).set_duration(video.duration)
    except Exception:
        pass

    # optional audio
    audio = meta.get("audio")
    if audio:
        audio_path = normalize_path(audio, repo_root)
        if audio_path.exists():
            a = AudioFileClip(str(audio_path))
            if a.duration < video.duration:
                loops, dur = [], 0.0
                while dur < video.duration:
                    seg = a.subclip(0, min(a.duration, video.duration - dur))
                    loops.append(seg)
                    dur += seg.duration
                a = concatenate_audioclips(loops).set_duration(video.duration)
            else:
                a = a.subclip(0, video.duration)
            video = video.set_audio(a)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(str(out_path), fps=fps, codec="libx264", audio_codec="aac", preset="medium", threads=4)

if __name__ == "__main__":
    main()
