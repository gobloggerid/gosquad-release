#!/bin/bash
set -euo pipefail

if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
else
    echo "No Python 3.13 interpreter found. Install python3.13 and retry."
    exit 1
fi

GAME_DIR=$(pwd)
PACKAGES_DIR="$GAME_DIR/dist/ba_data/python-site-packages"
mkdir -p "$PACKAGES_DIR"

echo "Creating virtual environment...."
sleep 2

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate

echo "Installing packages...."
sleep 2

python -m pip install --upgrade pip
python -m pip install --upgrade \
    --target="$PACKAGES_DIR" \
    better-profanity==0.6.1 \
    "redis[hiredis]" \
    unidecode \
    requests \
    rich \
    pynacl \
    psutil \
    discord

echo "✅ Packages installation complete!"
echo "Please run the next step!"