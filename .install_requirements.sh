#!/bin/bash

set -euo pipefail

if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "No Python 3 interpreter found. Install python3.13 or python3 and retry."
    exit 1
fi

TARGET_DIR="dist/ba_data/python-site-packages"
mkdir -p "$TARGET_DIR"

"$PYTHON_BIN" -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --upgrade \
    --target="$TARGET_DIR" \
    better-profanity==0.6.1 \
    "redis[hiredis]" \
    unidecode \
    requests \
    rich \
    psutil \
    discord

