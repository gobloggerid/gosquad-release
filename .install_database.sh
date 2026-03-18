#!/bin/bash
set -e

USER=$(whoami)
GAME_DIR=$(pwd)
MODS_DIR="$GAME_DIR/dist/ba_root/mods"
SEED_DIR="$MODS_DIR/seed"

if [[ "$USER" == "root" ]]; then
    echo "❌ Do not run as root."
    exit 1
fi

# Check if systemd is available
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet systemd; then
    USE_SYSTEMCTL=true
else
    USE_SYSTEMCTL=false
fi

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor --batch --yes -o /etc/apt/keyrings/redis.gpg

echo "deb [signed-by=/etc/apt/keyrings/redis.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | \
sudo tee /etc/apt/sources.list.d/redis.list > /dev/null

sudo apt update
sudo apt install -y redis

# Stop Redis
if $USE_SYSTEMCTL; then
    sudo systemctl stop redis-server
else
    sudo service redis-server stop || sudo /etc/init.d/redis-server stop
fi

if redis-check-rdb "$SEED_DIR/gosquad.rdb"; then
    sudo cp --update --verbose "$SEED_DIR/gosquad.rdb" /var/lib/redis/gosquad.rdb
    sudo chown redis:redis /var/lib/redis/gosquad.rdb
    sudo chmod 660 /var/lib/redis/gosquad.rdb
else
    echo "❌ Invalid gosquad.rdb file. Aborting."
    exit 1
fi

if $USE_SYSTEMCTL; then
    CONF_UNIX="$SEED_DIR/.redis_unix.conf"
    CONF_TCP="$SEED_DIR/.redis_tcp.conf"
    echo "ℹ Using systemd Redis configs."
else
    CONF_UNIX="$SEED_DIR/.redis_unix_sysv.conf"
    CONF_TCP="$SEED_DIR/.redis_tcp_sysv.conf"
    echo "ℹ Using sysvinit/non-systemd Redis configs."
fi

sudo cp --update --verbose /etc/redis/redis.conf /etc/redis/redis.conf.orig
sudo cp "$CONF_UNIX" /etc/redis/redis.conf
sudo chown root:redis /etc/redis/redis.conf
sudo chmod 640 /etc/redis/redis.conf

sudo cp --update --verbose "$SEED_DIR/.gosquad.acl" /etc/redis/gosquad.acl
sudo chown redis:redis /etc/redis/gosquad.acl
sudo chmod 640 /etc/redis/gosquad.acl

# Ensure /run/redis exists (for non-systemd systems)
sudo mkdir -p /run/redis
sudo chown redis:redis /run/redis
sudo chmod 755 /run/redis

# Add current user to redis group (requires re-login)
sudo usermod -aG redis "$USER"

# Start Redis
if $USE_SYSTEMCTL; then
    sudo systemctl restart redis-server
else
    sudo service redis-server restart || sudo /etc/init.d/redis-server restart
fi
sleep 2

echo "🔎 Testing connection..."
if redis-cli -s /run/redis/redis.sock ping; then
    echo "✅ Redis is responding via socket."
else
    echo "⚠ Socket connection failed. Switching to TCP config..."
    sudo cp "$CONF_TCP" /etc/redis/redis.conf
    sudo chown root:redis /etc/redis/redis.conf
    sudo chmod 640 /etc/redis/redis.conf

    if $USE_SYSTEMCTL; then
        sudo systemctl restart redis-server
    else
        sudo service redis-server restart || sudo /etc/init.d/redis-server restart
    fi
    sleep 2

    if redis-cli -p 6379 ping; then
        echo "✅ Redis is responding via TCP on port 6379."
        echo "✅ Disable unixsocket in dist/ba_root/mods/data/live/configs/setting.json dbSettings.unixsocket"
    else
        echo "❌ Redis is not responding. Check configuration."
        exit 1
    fi
fi

echo "✅ Gosquad database installation complete!"
echo "System will reboot in 5 seconds..."
sleep 5
sudo reboot
