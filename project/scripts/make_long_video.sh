#!/usr/bin/env bash
# usage:
# bash make_long_video.sh <images_dir> <voiceover.mp3|NONE> <out.mp4> <duration_seconds_if_no_audio>
set -euo pipefail

IMAGES_DIR="${1:?images_dir}"
VOICE="${2:-NONE}"
OUT="${3:?out.mp4}"
DUR="${4:-600}" # 10 دقائق افتراضيًا

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# اصنع لستة صور
ls "$IMAGES_DIR"/*.{png,jpg,jpeg} >/dev/null 2>&1 || { echo "No images in $IMAGES_DIR"; exit 1; }
ls "$IMAGES_DIR"/*.{png,jpg,jpeg} 2>/dev/null | nl -v 1 | while read n f; do
  printf "file '%s'\nduration 6\n" "$f"
done > "$TMP/list.txt"

# آخر صورة تتكرر لحظة بسيطة (حيلة لـ ffmpeg concat)
LAST="$(tail -n1 "$TMP/list.txt" | awk '{print $2}' | tr -d "'")"
echo "file '$LAST'" >> "$TMP/list.txt"

# فيديو من الصور (تحريك بطيء بسيط عبر filter زوم خفيف)
ffmpeg -y -f concat -safe 0 -i "$TMP/list.txt" -vf "scale=1920:-2,zoompan=z='min(zoom+0.0003,1.05)':d=125" -r 30 -pix_fmt yuv420p "$TMP/video.mp4"

if [ "$VOICE" != "NONE" ]; then
  # ملائمة طول الفيديو للصوت
  A_DUR=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$VOICE")
  ffmpeg -y -stream_loop -1 -i "$TMP/video.mp4" -i "$VOICE" -shortest -c:v libx264 -c:a aac -b:a 192k -pix_fmt yuv420p "$OUT"
else
  # بدون صوت — قص على مدة محددة
  ffmpeg -y -i "$TMP/video.mp4" -t "$DUR" -c:v libx264 -pix_fmt yuv420p "$OUT"
fi

echo "Long video => $OUT"
