#!/bin/bash
set -e

USER=$(whoami)
MODS_DIR="$GAME_DIR/dist/ba_root/mods"
SEED_DIR="$MODS_DIR/seed"

if [[ "$USER" == "root" ]]; then
    echo "❌ Do not run as root."
    exit 1
fi

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor --batch --yes -o /etc/apt/keyrings/redis.gpg

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
sleep 2

echo "✅ Gosquad database installation complete!."

echo "✅ The system will reboot to take effect. Please reconnect."
sleep 5
sudo reboot