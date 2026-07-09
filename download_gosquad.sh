#!/usr/bin/env bash
set -euo pipefail

REPO="n00bility/gosquad"

ARCH="$(uname -m)"

case "$ARCH" in
    x86_64)          ASSET="gosquad-x86_64.tar.gz" ;;
    aarch64|arm64)   ASSET="gosquad-arm64.tar.gz" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

URL="https://github.com/${REPO}/releases/latest/download/${ASSET}"

echo "Architecture : $ARCH"
echo "Downloading and extracting..."

curl -L --fail "$URL" | tar -xz

echo "Done."
