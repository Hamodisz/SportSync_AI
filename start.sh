#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

echo "[start] python: $(python --version)"
echo "[start] cwd: $(pwd)"
echo "[start] PORT=${PORT:-10000}"

# معلومة سريعة
which ffmpeg || echo "[warn] ffmpeg not found (مو ضروري حالياً)"

# شغّل ستريملت على بورت Render
exec streamlit run app_streamlit.py \
  --server.port="${PORT:-10000}" \
  --server.address=0.0.0.0 \
  --server.headless=true
