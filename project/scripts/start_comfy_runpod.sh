#!/usr/bin/env bash
# يجهز ComfyUI على بود RunPod (أو أي سيرفر) + إضافات أساسية ويشغل السيرفر على 0.0.0.0:8188
# usage (Start Command في RunPod image):
#   bash project/scripts/start_comfy_runpod.sh
set -euo pipefail

# مسارات افتراضية (عدّلها لو حاب)
ROOT="${ROOT:-/workspace}"                    # بعض صور RunPod تستخدم /workspace
APP_DIR="${APP_DIR:-$ROOT/ComfyUI}"
CN_DIR="${CN_DIR:-$APP_DIR/custom_nodes}"
OUT_DIR="${OUT_DIR:-$ROOT/project/outputs}"
JOB_DIR="${JOB_DIR:-$ROOT/project/jobs}"

# أنشئ مجلدات مشروع افتراضية
mkdir -p "$ROOT/project/scripts" "$OUT_DIR" "$JOB_DIR" \
         "$ROOT/project/videos/long" "$ROOT/project/videos/shorts" \
         "$ROOT/project/audio/voiceovers" "$ROOT/project/markers"

# تثبيت أدوات
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

# تثبيت متطلبات بايثون
python3 -m pip install --upgrade pip
python3 -m pip install requests tqdm pillow

# تثبيت إضافات مهمة (لو مو مثبتة)
mkdir -p "$CN_DIR"
if [ ! -d "$CN_DIR/ComfyUI-Manager" ]; then
  git clone https://github.com/ltdrdata/ComfyUI-Manager.git "$CN_DIR/ComfyUI-Manager"
fi
if [ ! -d "$CN_DIR/ComfyUI-Impact-Pack" ]; then
  git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git "$CN_DIR/ComfyUI-Impact-Pack"
fi
if [ ! -d "$CN_DIR/ComfyUI-VideoHelperSuite" ]; then
  git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "$CN_DIR/ComfyUI-VideoHelperSuite"
fi

# موديلات (نزّلها من داخل ComfyUI-Manager أو يدويًا لاحقًا)
mkdir -p "$APP_DIR/models"

# إعدادات ComfyUI
export COMFYUI_PATH="$APP_DIR"
export CLI_ARGS="${CLI_ARGS:---listen 0.0.0.0 --port 8188 --enable-cors-header *}"

echo "==> Starting ComfyUI at 0.0.0.0:8188"
cd "$APP_DIR"
python3 main.py $CLI_ARGS
