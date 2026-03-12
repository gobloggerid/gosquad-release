#!/bin/bash
set -euo pipefail

cleanup() {
    rc=$?

    if [ "$rc" -eq 0 ]; then
        sync
        echo "✅ Script completed successfully. Rebooting..."
        sudo reboot
    else
        echo "❌ Script failed (exit $rc). Not rebooting."
    fi
}

trap cleanup EXIT
trap 'exit 1' INT TERM

USER=$(whoami)
GAME_DIR=$(pwd)
MODS_DIR="$GAME_DIR/dist/ba_root/mods"
SEED_DIR="$MODS_DIR/seed"
DATA_DIR="$MODS_DIR/data"
DEFAULTS_DIR="$DATA_DIR/defaults"
LIVE_DIR="$DATA_DIR/live"
PACKAGES_DIR="$GAME_DIR/dist/ba_data/python-site-packages"

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

echo "Preparing necessary files..."
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
echo ""

echo "⏳ Preparing for the next step..."
sleep 2

echo "Installing python...."
echo ""

sudo apt update && sudo apt upgrade -y
sudo apt install software-properties-common -y
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.13-dev python3.13-venv python3-pip

echo "✅ Done installing python."
echo ""

echo "⏳ Preparing for the next step..."
sleep 2

echo "Installing database...."
echo ""

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/redis.gpg

echo "deb [signed-by=/etc/apt/keyrings/redis.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | \
sudo tee /etc/apt/sources.list.d/redis.list > /dev/null

sudo apt update
sudo apt install -y redis

sudo systemctl stop redis-server

if redis-check-rdb "$SEED_DIR/gosquad.rdb"; then
    sudo cp --update --verbose "$SEED_DIR/gosquad.rdb" /var/lib/redis/gosquad.rdb
    sudo chown redis:redis /var/lib/redis/gosquad.rdb
    sudo chmod 660 /var/lib/redis/gosquad.rdb
else
    echo "❌ Invalid gosquad.rdb file. Aborting."
    exit 1
fi

sudo cp --update --verbose /etc/redis/redis.conf /etc/redis/redis.conf.orig
sudo cp "$SEED_DIR/.redis.conf" /etc/redis/redis.conf
sudo chown root:redis /etc/redis/redis.conf
sudo chmod 640 /etc/redis/redis.conf

sudo cp --update --verbose "$SEED_DIR/.gosquad.acl" /etc/redis/gosquad.acl
sudo chown redis:redis /etc/redis/gosquad.acl
sudo chmod 640 /etc/redis/gosquad.acl

sudo usermod -aG redis "$USER"
sudo systemctl restart redis-server

echo "✅ Gosquad database installation complete!"
echo ""

echo "⏳ Preparing for the next step..."
sleep 2

echo "Installing packages...."
echo ""

if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "No Python 3 interpreter found. Install python3.13 or python3 and retry."
    exit 1
fi

mkdir -p "$PACKAGES_DIR"

pip3.13 install --upgrade pip
pip3.13 install --upgrade \
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
echo ""

echo "✅ The system will reboot to take effect. Please reconnect."
sleep 4
