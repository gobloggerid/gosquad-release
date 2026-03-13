#!/bin/bash
set -euo pipefail

USER=$(whoami)
GAME_DIR=$(pwd)
MODS_DIR="$GAME_DIR/dist/ba_root/mods"
SEED_DIR="$MODS_DIR/seed"
DATA_DIR="$MODS_DIR/data"
DEFAULTS_DIR="$DATA_DIR/defaults"
LIVE_DIR="$DATA_DIR/live"

if [[ "$USER" == "root" ]]; then
    echo "❌ Please do not run this script as root."
    exit 1
fi

if [[ ! -d "$MODS_DIR" ]]; then
    echo "❌ Source directory not found: $MODS_DIR"
    exit 1
fi

if [[ ! -d "$SEED_DIR" ]]; then
    echo "❌ Source directory not found: $SEED_DIR"
    exit 1
fi

if [[ ! -d "$DATA_DIR" ]]; then
    echo "❌ Source directory not found: $DATA_DIR"
    exit 1
fi

echo "⏳ Preparing necessary files..."
sleep 2
echo ""

cp --update --verbose --target-directory ./ "$SEED_DIR/gosquad_server"
cp --update --verbose --target-directory ./dist "$SEED_DIR/gosquad_headless" "$SEED_DIR/gosquad_headless_aarch64"

mkdir -p \
    "$LIVE_DIR" \
    "$LIVE_DIR/characters" \
    "$LIVE_DIR/configs" \
    "$LIVE_DIR/languages" \
    "$LIVE_DIR/playlists" \
    "$LIVE_DIR/text" \
    "$DATA_DIR/logs" \
    "$DATA_DIR/state"

[[ -f "$DEFAULTS_DIR/playlists/config.toml" ]] && cp --update --verbose --target-directory "$LIVE_DIR/playlists/" "$DEFAULTS_DIR/playlists/config.toml"
[[ -d "$DEFAULTS_DIR/configs" ]] && cp --update --verbose --target-directory "$LIVE_DIR/configs/" "$DEFAULTS_DIR/configs/"*.json || true
[[ -d "$DEFAULTS_DIR/textlibs" ]] && cp --update --verbose --target-directory "$LIVE_DIR/text/" "$DEFAULTS_DIR/textlibs/"*.txt || true

[[ -f "gosquad_server" ]] && chmod 700 "gosquad_server"
[[ -f "./dist/gosquad_headless" ]] && chmod 700 "./dist/gosquad_headless"
[[ -f "./dist/gosquad_headless_aarch64" ]] && chmod 700 "./dist/gosquad_headless_aarch64"

sudo chown -R "$USER:$USER" "$GAME_DIR"
echo "✅ Fix files ownership..."
echo ""

echo "✅ Done preparing all necessary files."
echo "Please run the next step!"