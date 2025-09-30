# logic/video_pipeline.py
"""
تحويل مجلد صور (scene_*.png) إلى فيديو عمودي 1080x1920
Usage (CLI):
python logic/video_pipeline.py --images outputs/gha_short_work --out outputs/gha_short_work/short_no_audio.mp4 --seconds 1.2 --fps 30 --audio tmp/audio_in.mp3
Requirements:
pip install moviepy imageio-ffmpeg
ffmpeg must be installed on system
"""

import sys
from pathlib import Path
import argparse
import logging
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def find_images(images_dir: Path, pattern: str = "scene_*.png"):
    images = sorted(images_dir.glob(pattern))
    return images


def build_video_from_images(images, output_path: Path, seconds_per_image: float = 1.2, fps: int = 30, audio_path: Path | None = None, size=(1080, 1920)):
    if not images:
        raise ValueError("No images found to build video.")

    logging.info("Preparing %d clips (each %.2fs)", len(images), seconds_per_image)
    clips = []
    for img in images:
        p = img.resolve()
        if not p.exists():
            logging.error("Image missing: %s", p)
            raise FileNotFoundError(p)
        clip = ImageClip(str(p)).set_duration(seconds_per_image)
        # resize to fill (cover) target size while keeping aspect ratio
        clip = clip.resize(height=size[1])
        if clip.w < size[0]:
            clip = clip.resize(width=size[0])
        # center
        clip = clip.set_position("center")
        clip = clip.on_color(size=size, color=(0, 0, 0), pos=("center", "center"))
        clips.append(clip)

    logging.info("Concatenating %d clips", len(clips))
    final = concatenate_videoclips(clips, method="compose")

    # optional audio
    if audio_path:
        audio_path = audio_path.resolve()
        if audio_path.exists():
            logging.info("Attaching audio: %s", audio_path)
            audio = AudioFileClip(str(audio_path)).subclip(0, final.duration)
            final = final.set_audio(audio)
        else:
            logging.warning("Audio file not found: %s (continuing without audio)", audio_path)

    # write file
    logging.info("Writing output video to: %s", output_path)
    final.write_videofile(str(output_path), fps=fps, codec="libx264", audio_codec="aac", preset="medium", threads=4)
    logging.info("Done writing video.")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--images", required=True, help="Folder containing scene_*.png images")
    p.add_argument("--out", required=True, help="Output mp4 path")
    p.add_argument("--seconds", type=float, default=1.2, help="Seconds per image")
    p.add_argument("--fps", type=int, default=30, help="FPS for output")
    p.add_argument("--audio", default=None, help="Optional audio file path")
    return p.parse_args()


def main():
    args = parse_args()
    images_dir = Path(args.images)
    out_path = Path(args.out)
    seconds = args.seconds
    fps = args.fps
    audio = Path(args.audio) if args.audio else None

    logging.info("Images dir: %s", images_dir.resolve() if images_dir.exists() else images_dir)
    if not images_dir.exists():
        logging.error("Images directory does not exist: %s", images_dir)
        sys.exit(1)

    images = find_images(images_dir)
    if not images:
        logging.error("No images matching scene_*.png in %s", images_dir)
        sys.exit(1)

    try:
        build_video_from_images(images, out_path, seconds, fps, audio)
    except Exception as e:
        logging.exception("Video build failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
