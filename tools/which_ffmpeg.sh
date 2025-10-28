#!/usr/bin/env bash
set -e
# 1) لو في PATH
if command -v ffmpeg >/dev/null 2>&1; then
  command -v ffmpeg
  exit 0
fi

# 2) في المجلدات المضمّنة
for cand in \
  "vendor/ffmpeg/linux/ffmpeg" \
  "vendor/ffmpeg/macos/ffmpeg" \
  "vendor/ffmpeg/win/ffmpeg.exe"
do
  if [ -x "$cand" ]; then
    echo "$cand"
    exit 0
  fi
done

echo "FFMPEG_NOT_FOUND" >&2
exit 1
