#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYBIN="${PYBIN:-python3}"
exec "$PYBIN" -m streamlit run "$SCRIPT_DIR/app.py" --server.address=0.0.0.0 --server.port=8501