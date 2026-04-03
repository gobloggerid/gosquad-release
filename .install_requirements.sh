#!/bin/bash

set -euo pipefail

if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
else
    echo "No Python 3.13 interpreter found. Install python3.13 and retry."
    exit 1
fi

TARGET_DIR="dist/ba_data/python-site-packages"
mkdir -p "$TARGET_DIR"

"$PYTHON_BIN" -m venv venv
source venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
# Note: gosquad-private: install to virtual environment,
# gosquad: install to target directory (for bundling with game)
echo "Installing dependencies to virtual environment..."
python -m pip install --upgrade \
    better-profanity==0.6.1 \
    "redis[hiredis]" \
    unidecode \
    requests \
    rich \
    cffi \
    cryptography \
    psutil \
    discord
