#!/usr/bin/env bash
# يصنع فيديو طويل (سلايد شو) من صور + تعليق صوتي اختياري.
# usage:
#   bash make_long_video.sh <images_dir> <voiceover.mp3|none> <out.mp4> <target_seconds> [fps=30] [size=1920x1080]
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "usage: $0 <images_dir> <voiceover.mp3|none> <out.mp4> <target_seconds> [fps=30] [size=1920x1080]"
  exit 1
fi

IM_DIR="$1"
VOICE="$2"
OUT="$3"
TARGET="${4}"
FPS="${5:-30}"
SIZE="${6:-1920x1080}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg غير مثبت"; exit 2
fi

if [ ! -d "$IM_DIR" ]; then
  echo "images_dir غير موجود: $IM_DIR"; exit 3
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# اجمع الصور (png/jpg/jpeg/webp)
mapfile -t IMAGES < <(find "$IM_DIR" -maxdepth 1 -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | sort -V)
CNT="${#IMAGES[@]}"

if [ "$CNT" -eq 0 ]; then
  echo "لا توجد صور في $IM_DIR"; exit 4
fi

# احسب مدة كل صورة
# إن كان الصوت موجودًا وتبغى تضبط الدقائق عليه، تقدر تحسب مدته وتعدل هنا.
PER_IMG=$(python3 - <<PY
n = $CNT
t = float("$TARGET")
print(max(1.0, t / n))
PY
)

# أنشئ مقاطع لكل صورة (loop + scale) ثم concat
i=0
for img in "${IMAGES[@]}"; do
  seg="$TMP/seg_$i.mp4"
  ffmpeg -v error -y -loop 1 -t "$PER_IMG" -i "$img" \
    -vf "scale=${SIZE}:force_original_aspect_ratio=decrease,pad=${SIZE}:(ow-iw)/2:(oh-ih)/2" \
    -r "$FPS" -c:v libx264 -tune stillimage -pix_fmt yuv420p "$seg"
  echo "file '$seg'" >> "$TMP/concat.txt"
  i=$((i+1))
done

ffmpeg -v error -y -f concat -safe 0 -i "$TMP/concat.txt" -c copy "$TMP/video_noaudio.mp4"

# أضف الصوت (اختياري)
if [ "$VOICE" != "none" ] && [ -f "$VOICE" ]; then
  ffmpeg -v error -y -i "$TMP/video_noaudio.mp4" -i "$VOICE" \
    -c:v copy -c:a aac -shortest -movflags +faststart "$OUT"
else
  # صامت بطول الهدف
  ffmpeg -v error -y -i "$TMP/video_noaudio.mp4" -t "$TARGET" -c:v copy -an -movflags +faststart "$OUT"
fi

echo "[OK] صنع الفيديو: $OUT"
