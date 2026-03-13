#!/usr/bin/env bash
set -Eeuo pipefail

trap 'rc=$?; [[ $rc == 0 ]] && echo "✅ Script completed successfully." || echo "❌ Script failed (exit $rc).";' EXIT

log() {
echo ""
echo "▶ $1"
}

require_dir() {
[[ -d "$1" ]] || { echo "❌ Missing directory: $1"; exit 1; }
}

USER=$(whoami)
GAME_DIR=$(pwd)

MODS_DIR="$GAME_DIR/dist/ba_root/mods"
SEED_DIR="$MODS_DIR/seed"
DATA_DIR="$MODS_DIR/data"
DEFAULTS_DIR="$DATA_DIR/defaults"
LIVE_DIR="$DATA_DIR/live"
PACKAGES_DIR="$GAME_DIR/dist/ba_data/python-site-packages"

if [[ "$USER" == "root" ]]; then
echo "❌ Please run this script as a normal user."
exit 1
fi

# RAM safety check

RAM=$(free -m | awk '/Mem:/ {print $2}')
if [[ "$RAM" -lt 512 ]]; then
echo "❌ Gosquad requires at least 512MB RAM."
exit 1
fi

require_dir "$MODS_DIR"
require_dir "$SEED_DIR"
require_dir "$DATA_DIR"

log "Preparing files"

cp -u "$SEED_DIR/gosquad_server" .
cp -u "$SEED_DIR/gosquad_headless"* ./dist/

mkdir -p
"$LIVE_DIR"/{characters,configs,languages,playlists,text}
"$DATA_DIR"/{logs,state}

cp -u "$DEFAULTS_DIR/playlists/config.toml" "$LIVE_DIR/playlists/" 2>/dev/null || true
cp -u "$DEFAULTS_DIR/configs/"*.json "$LIVE_DIR/configs/" 2>/dev/null || true
cp -u "$DEFAULTS_DIR/textlibs/"*.txt "$LIVE_DIR/text/" 2>/dev/null || true

chmod 700 gosquad_server 2>/dev/null || true
chmod 700 ./dist/gosquad_headless* 2>/dev/null || true

sudo chown -R "$USER:$USER" "$GAME_DIR"

log "Installing system dependencies"

command -v sudo >/dev/null || apt install -y sudo

export DEBIAN_FRONTEND=noninteractive

sudo apt update
sudo apt install -y
curl
gnupg
lsb-release
ca-certificates
build-essential
software-properties-common

source /etc/os-release

log "Detecting Python"

if command -v python3.13 >/dev/null 2>&1; then
PYTHON_BIN=python3.13

elif command -v python3 >/dev/null 2>&1; then
PYTHON_BIN=python3

else

```
log "Installing Python"

if [[ "$ID" == "ubuntu" ]]; then
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.13 python3.13-dev python3.13-venv python3-pip
    PYTHON_BIN=python3.13

elif [[ "$ID" == "debian" ]]; then
    sudo apt install -y python3 python3-dev python3-venv python3-pip
    PYTHON_BIN=python3

else
    echo "❌ Unsupported distribution: $ID"
    exit 1
fi
```

fi

log "Using Python: $PYTHON_BIN"

log "Checking Redis installation"

if systemctl list-unit-files | grep -q redis-server; then
log "Redis already installed"
else

```
log "Installing Redis"

sudo mkdir -p /etc/apt/keyrings

curl -fsSL https://packages.redis.io/gpg | \
sudo gpg --dearmor -o /etc/apt/keyrings/redis.gpg

if [[ ! -f /etc/apt/sources.list.d/redis.list ]]; then
    echo "deb [signed-by=/etc/apt/keyrings/redis.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | \
    sudo tee /etc/apt/sources.list.d/redis.list > /dev/null
fi

sudo apt update
sudo apt install -y redis redis-tools
```

fi

sudo systemctl stop redis-server

if redis-check-rdb "$SEED_DIR/gosquad.rdb"; then
sudo cp -u "$SEED_DIR/gosquad.rdb" /var/lib/redis/gosquad.rdb
sudo chown redis:redis /var/lib/redis/gosquad.rdb
sudo chmod 660 /var/lib/redis/gosquad.rdb
else
echo "❌ Invalid gosquad.rdb file."
exit 1
fi

sudo cp -u /etc/redis/redis.conf /etc/redis/redis.conf.orig
sudo cp "$SEED_DIR/.redis.conf" /etc/redis/redis.conf
sudo chown root:redis /etc/redis/redis.conf
sudo chmod 640 /etc/redis/redis.conf

sudo cp -u "$SEED_DIR/.gosquad.acl" /etc/redis/gosquad.acl
sudo chown redis:redis /etc/redis/gosquad.acl
sudo chmod 640 /etc/redis/gosquad.acl

if ! groups "$USER" | grep -q redis; then
sudo usermod -aG redis "$USER"
fi

sudo systemctl restart redis-server

log "Installing Python packages"

mkdir -p "$PACKAGES_DIR"

"$PYTHON_BIN" -m pip install --upgrade pip

"$PYTHON_BIN" -m pip install
--upgrade
--target="$PACKAGES_DIR"
better-profanity==0.6.1
"redis[hiredis]"
unidecode
requests
rich
pynacl
psutil
discord

log "Setup finished"

echo ""
read -p "Reboot now? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] && sudo reboot
