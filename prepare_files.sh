#!/bin/bash
set -euo pipefail

USER=$(whoami)
GAME_DIR=$(pwd)
SEED_DIR="$GAME_DIR/seed"
MODS_DIR="$GAME_DIR/dist/ba_root/mods"

if [[ "$USER" == "root" ]]; then
    echo "❌ Please do not run this script as root."
    exit 1
fi

if [[ ! -d "$SEED_DIR" ]]; then
    echo "❌ Source directory not found: $SEED_DIR"
    exit 1
fi

cp --no-clobber --verbose --target-directory ./ "$SEED_DIR/gosquad_server"
cp --no-clobber --verbose --target-directory ./dist "$SEED_DIR/gosquad_headless" "$SEED_DIR/gosquad_headless_aarch64"

cp --no-clobber --verbose --target-directory "$MODS_DIR/" "$MODS_DIR/playlists"/{config.toml,smash.toml,fight.toml,ffa.toml,team.toml,duel.toml,sport.toml}

cp --no-clobber --verbose --target-directory ./dist/ba_root/ "$MODS_DIR/configs/config.json"

cp --no-clobber --verbose --target-directory "$MODS_DIR/" "$MODS_DIR/configs/setting.json"

[[ -f "gosquad_server" ]] && chmod 700 "gosquad_server"
[[ -f "./dist/gosquad_headless" ]] && chmod 700 "./dist/gosquad_headless"
[[ -f "./dist/gosquad_headless_aarch64" ]] && chmod 700 "./dist/gosquad_headless_aarch64"

for f in "$MODS_DIR/config.toml" "$MODS_DIR/smash.toml" "$MODS_DIR/fight.toml" "$MODS_DIR/ffa.toml" "$MODS_DIR/team.toml" "$MODS_DIR/duel.toml" "$MODS_DIR/sport.toml"; do
    [[ -f "$f" ]] && chmod 600 "$f"
done

echo "✅ Fix files ownership..."
sudo chown -R "$USER:$USER" "$GAME_DIR"

echo "✅ Done preparing all necessary files."
