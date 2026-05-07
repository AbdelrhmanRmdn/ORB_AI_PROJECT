#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

sudo apt update
sudo apt install -y \
  python3-venv python3-pip python3-dev \
  build-essential cmake pkg-config \
  libopenblas-dev liblapack-dev \
  libjpeg-dev libpng-dev \
  portaudio19-dev espeak-ng \
  libatlas-base-dev libhdf5-dev \
  libcamera-apps

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo "Bootstrap complete. Activate with: source .venv/bin/activate"
