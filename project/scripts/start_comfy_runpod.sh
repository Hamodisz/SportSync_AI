#!/usr/bin/env bash
# يجهز ComfyUI + إضافات أساسية ويشغل السيرفر على 0.0.0.0:8188
set -euo pipefail

ROOT="${ROOT:-/workspace}"
APP_DIR="${APP_DIR:-$ROOT/ComfyUI}"
CN_DIR="${CN_DIR:-$APP_DIR/custom_nodes}"
OUT_DIR="${OUT_DIR:-$ROOT/project/outputs}"
JOB_DIR="${JOB_DIR:-$ROOT/project/jobs}"

mkdir -p "$ROOT/project/scripts" "$OUT_DIR" "$JOB_DIR" \
         "$ROOT/project/videos/long" "$ROOT/project/videos/shorts" \
         "$ROOT/project/audio/voiceovers" "$ROOT/project/markers"

if ! command -v git >/dev/null 2>&1; then
  apt-get update && apt-get install -y git
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  apt-get update && apt-get install -y ffmpeg
fi
if ! command -v python3 >/dev/null 2>&1; then
  apt-get update && apt-get install -y python3 python3-pip
fi

# جلب ComfyUI إن غير موجود
if [ ! -d "$APP_DIR" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$APP_DIR"
fi

python3 -m pip install --upgrade pip
python3 -m pip install requests tqdm pillow

# إضافات مشهورة
mkdir -p "$CN_DIR"
[ ! -d "$CN_DIR/ComfyUI-Manager" ] && git clone https://github.com/ltdrdata/ComfyUI-Manager.git "$CN_DIR/ComfyUI-Manager"
[ ! -d "$CN_DIR/ComfyUI-Impact-Pack" ] && git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git "$CN_DIR/ComfyUI-Impact-Pack"
[ ! -d "$CN_DIR/ComfyUI-VideoHelperSuite" ] && git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "$CN_DIR/ComfyUI-VideoHelperSuite"

mkdir -p "$APP_DIR/models"

export COMFYUI_PATH="$APP_DIR"
export CLI_ARGS="${CLI_ARGS:---listen 0.0.0.0 --port 8188 --enable-cors-header *}"

echo "==> Starting ComfyUI at 0.0.0.0:8188"
cd "$APP_DIR"
python3 main.py $CLI_ARGS
