#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
exec streamlit run app_streamlit.py --server.port="${PORT:-10000}" --server.address=0.0.0.0 --server.headless=true
