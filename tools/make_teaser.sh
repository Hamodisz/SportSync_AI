#!/usr/bin/env bash
set -euo pipefail

FFMPEG_BIN="$(bash tools/which_ffmpeg.sh || true)"
export FFMPEG_BIN
if [ -z "${FFMPEG_BIN}" ] || [ "${FFMPEG_BIN}" = "FFMPEG_NOT_FOUND" ]; then
  echo "❌ لا يوجد ffmpeg في PATH ولا في vendor/. إمّا شغّل داخل Docker أو ضع binary في vendor/ffmpeg/."
  exit 2
fi

FONT_PATH="$(bash tools/which_font.sh || true)"
USE_DRAW=1
if [ -z "${FONT_PATH}" ] || [ "${FONT_PATH}" = "FONT_NOT_FOUND" ]; then
  echo "ℹ لا يوجد خط متاح، سنكمل بدون نصوص مرسومة."
  USE_DRAW=0
fi

mkdir -p build

# اجمع الصور من المجلدات المحلية فقط
if [ ! -f build/inputs.txt ]; then
  python3 - <<'PY'
import glob
import pathlib
import sys

roots = ["assets/video","assets/images","assets","media","static","public","images"]
paths = []
for root in roots:
    p = pathlib.Path(root)
    if p.exists():
        for ext in ("*.png","*.jpg","*.jpeg","*.webp"):
            paths.extend(glob.glob(str(p / ext)))
paths = sorted(set(paths))[:8]
if not paths:
    sys.exit("NO_LOCAL_ASSETS_FOUND")
duration = 6.0 / max(1, len(paths))
with open("build/inputs.txt", "w", encoding="utf-8") as f:
    for p in paths:
        f.write(f"file '{pathlib.Path(p).resolve()}'\n")
        f.write(f"duration {duration:.3f}\n")
print(f"ASSETS={len(paths)} DUR_PER_IMAGE={duration:.3f}")
PY
fi

# _base.mp4 (إذا ناقص أو inputs أحدث)
NEED_BASE=1
if [ -f build/_base.mp4 ] && [ -f build/inputs.txt ]; then
  if [ build/_base.mp4 -nt build/inputs.txt ]; then NEED_BASE=0; fi
fi
if [ $NEED_BASE -eq 1 ]; then
  "${FFMPEG_BIN}" -y -f concat -safe 0 -i build/inputs.txt \
    -pix_fmt yuv420p \
    -vf "zoompan=z='min(zoom+0.0015,1.08)':d=60:s=1920x1080,scale=1920:1080" \
    -r 30 -t 6 -an build/_base.mp4
fi

# _video.mp4 مع/بدون نصوص
if [ ! -f build/_video.mp4 ] || [ build/_video.mp4 -ot build/_base.mp4 ]; then
  if [ $USE_DRAW -eq 1 ]; then
    "${FFMPEG_BIN}" -y -i build/_base.mp4 -vf \
    "drawtext=fontfile=${FONT_PATH}:text='SportSync · Unlock Your Motion DNA':x=40:y=60:fontsize=42:fontcolor=white:borderw=2:shadowx=2:shadowy=2,\
     drawtext=fontfile=${FONT_PATH}:text='Tailored guidance. Momentum that lasts.':x=(w-text_w-40):y=(h-text_h-60):fontsize=28:fontcolor=white:borderw=2:shadowx=2:shadowy=2" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -an -t 6 build/_video.mp4
  else
    cp build/_base.mp4 build/_video.mp4
  fi
fi

# دمج صوت إن وُجد
AUDIO=""
for a in media/audio theme audio assets/audio; do
  if [ -d "$a" ]; then
    CAND=$(ls -1 $a/*.mp3 2>/dev/null | head -n1 || true)
    [ -n "$CAND" ] && { AUDIO="$CAND"; break; }
  fi
done

if [ -n "$AUDIO" ]; then
  "${FFMPEG_BIN}" -y -i build/_video.mp4 -i "$AUDIO" -filter:a "volume=0.5" \
    -c:v copy -c:a aac -b:a 128k -shortest -t 6 build/sportsync_teaser_6s.mp4
else
  "${FFMPEG_BIN}" -y -i build/_video.mp4 -c copy -t 6 build/sportsync_teaser_6s.mp4
fi

# تحقق قبول
python3 - <<'PY'
import os
import pathlib
import re
import subprocess
import sys

ffmpeg = os.environ.get("FFMPEG_BIN")
video_path = pathlib.Path("build/sportsync_teaser_6s.mp4")
if not video_path.exists():
    print("❌ فشل التحقق: الملف غير موجود")
    sys.exit(1)

proc = subprocess.run(
    [ffmpeg, "-hide_banner", "-i", str(video_path)],
    capture_output=True,
    text=True
)
info = proc.stderr

match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", info)
if not match:
    print("❌ فشل التحقق: تعذّر قراءة المدة")
    sys.exit(1)

duration = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
video_line = next((line.strip() for line in info.splitlines() if "Video:" in line), "")
audio_line = next((line.strip() for line in info.splitlines() if "Audio:" in line), "")
size_mb = video_path.stat().st_size / (1024 * 1024)

ok = True
if not (5.95 <= duration <= 6.05):
    print(f"❌ فشل التحقق: المدة {duration:.3f}s خارج النطاق")
    ok = False
if "h264" not in video_line.lower():
    print(f"❌ فشل التحقق: كودك الفيديو غير h264 -> {video_line}")
    ok = False
if "yuv420p" not in video_line.lower():
    print(f"❌ فشل التحقق: PixFmt غير yuv420p -> {video_line}")
    ok = False
if "1920x1080" not in video_line.replace(" ", ""):
    print(f"❌ فشل التحقق: الدقة ليست 1920x1080 -> {video_line}")
    ok = False
if "30 fps" not in video_line and "30 tbr" not in video_line:
    print(f"❌ فشل التحقق: الإطار ليس 30fps -> {video_line}")
    ok = False
if audio_line:
    if "aac" not in audio_line.lower():
        print(f"❌ فشل التحقق: كودك الصوت ليس AAC -> {audio_line}")
        ok = False
    br = re.search(r"(\d+) kb/s", audio_line)
    if br and abs(int(br.group(1)) - 128) > 8:
        print(f"❌ فشل التحقق: معدل الصوت ليس ~128k -> {audio_line}")
        ok = False

if ok:
    print(f"✅ VIDEO_OK path=build/sportsync_teaser_6s.mp4 size={size_mb:.2f}MB")
    print("✅ DURATION_OK (=6s ±0.05s)")
    print("✅ YT_READY (h264/aac yuv420p 1080p30)")
else:
    sys.exit(1)
PY
