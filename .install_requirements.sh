#!/bin/bash

set -euo pipefail

TARGET_DIR="dist/ba_data/python-site-packages"
mkdir -p "$TARGET_DIR"

python3.13 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install --upgrade \
    --target="$TARGET_DIR" \
    better-profanity==0.6.1 \
    "redis[hiredis]" \
    unidecode \
    requests \
    rich \
    cffi \
    cryptography \
    psutil \
    discord

