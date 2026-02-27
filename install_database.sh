#!/bin/bash
set -e

USER=$(whoami)

if [[ "$USER" == "root" ]]; then
    echo "❌ Do not run as root."
    exit 1
fi

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/redis.gpg

echo "deb [signed-by=/etc/apt/keyrings/redis.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | \
sudo tee /etc/apt/sources.list.d/redis.list > /dev/null

sudo apt update
sudo apt install -y redis

sudo systemctl stop redis-server

if redis-check-rdb ./seed/gosquad.rdb; then
    sudo cp -n ./seed/gosquad.rdb /var/lib/redis/gosquad.rdb
    sudo chown redis:redis /var/lib/redis/gosquad.rdb
    sudo chmod 660 /var/lib/redis/gosquad.rdb
else
    echo "❌ Invalid gosquad.rdb file. Aborting."
    exit 1
fi

sudo cp -b /etc/redis/redis.conf /etc/redis/redis.conf.orig
sudo cp ./seed/redis.conf /etc/redis/redis.conf
sudo chown root:redis /etc/redis/redis.conf
sudo chmod 640 /etc/redis/redis.conf

sudo cp -b ./seed/gosquad.acl /etc/redis/gosquad.acl
sudo chown redis:redis /etc/redis/gosquad.acl
sudo chmod 640 /etc/redis/gosquad.acl

# Add current user to redis group (requires re-login)
sudo usermod -aG redis "$USER"

# Restart Redis
sudo systemctl restart redis-server

echo "✅ Gosquad database installation complete!."
echo "✅ Please log out and log back in for group changes to apply."
