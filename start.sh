#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
pip install --no-cache-dir -r requirements.txt
streamlit run app_streamlit.py --server.port ${PORT:-10000} --server.address 0.0.0.0
