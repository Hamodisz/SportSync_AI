# file: content_studio/ai_video/generate_final_video.py
import argparse
import json
import os
import tempfile
from pathlib import Path

# توافق MoviePy 1.x / 2.x
try:
    # MoviePy 2.x
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
except Exception:
    # MoviePy 1.x
    from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips  # type: ignore

import requests


def load_meta(p: str) -> dict:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_len_seconds(seconds, n_images):
    if not seconds or len(seconds) != n_images:
        # fallback: 5s لكل صورة
        return [5] * n_images
    return [max(0.5, float(s)) for s in seconds]


def text_overlay_clip(text, width, height, dur, margin=40):
    """
    يبني شريحة نص أسفل الصورة مع stroke بسيط. لو النص فاضي، يرجّع None.
    """
    txt = (text or "").strip()
    if not txt:
        return None

    # TextClip API نفسه في 1.x و 2.x
    clip = TextClip(
        txt,
        fontsize=60,
        color="white",
        stroke_color="black",
        stroke_width=3,
        method="caption",
        size=(int(width * 0.9), None),
    ).set_duration(dur).set_position(("center", height - margin - 200))  # قرب الأسفل
    return clip


def build_video(meta_path: str, out_path: str, width: int, height: int, audio_url: str = ""):
    meta = load_meta(meta_path)

    images = meta.get("images", [])
    texts = meta.get("texts", [])
    seconds = ensure_len_seconds(meta.get("seconds", []), len(images))

    if not images:
        raise ValueError("لا توجد صور في metadata.json")

    if len(texts) < len(images):
        texts += [""] * (len(images) - len(texts))

    size = (int(width), int(height))

    # تأكد من وجود الصور
    missing = [p for p in images if not Path(p).exists()]
    if missing:
        raise FileNotFoundError("الصور التالية غير موجودة:\n" + "\n".join(missing))

    clips = []
    for img_path, dur, txt in zip(images, seconds, texts):
        base = ImageClip(img_path).resize(newsize=size).set_duration(dur)
        txt_clip = text_overlay_clip(txt, width, height, dur)

        if txt_clip is not None:
            clip = CompositeVideoClip([base, txt_clip])
        else:
            clip = base

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")

    # صوت اختياري من URL
    if audio_url and audio_url.strip():
        with tempfile.TemporaryDirectory() as td:
            mp3_path = str(Path(td) / "audio.mp3")
            r = requests.get(audio_url, timeout=30)
            r.raise_for_status()
            with open(mp3_path, "wb") as f:
                f.write(r.content)
            narration = AudioFileClip(mp3_path)
            final = final.set_audio(narration)

            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac")
    else:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True, help="path to tmp/metadata.json")
    ap.add_argument("--out", required=True, help="output mp4 path")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--audio_url", default="", help="optional mp3/wav url")
    return ap.parse_args()


def main():
    args = parse_args()
    build_video(args.meta, args.out, args.width, args.height, args.audio_url)


if __name__ == "__main__":
    main()
