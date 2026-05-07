#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

python -m pip download -r requirements.txt -d wheelhouse
echo "Wheel cache created at $PROJECT_DIR/wheelhouse"
echo "Offline install command:"
echo "python -m pip install --no-index --find-links wheelhouse -r requirements.txt"
