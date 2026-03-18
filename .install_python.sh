#!/bin/bash
set -e

USER=$(whoami)

# Safety checks
if [[ "$USER" == "root" ]]; then
    echo "❌ Please do not run this script as root."
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
fi

# Update package list and upgrade
sudo apt update && sudo apt upgrade -y

if [[ "$DISTRO" == "ubuntu" ]]; then
    echo "📦 Installing Python 3.13 on Ubuntu..."
    # Install software properties common
    sudo apt install -y software-properties-common
    # Add deadsnakes PPA for Python 3.13
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    # Install Python 3.13 and related tools
    sudo apt install -y python3.13 python3.13-dev python3.13-venv python3.13-pip
    PYTHON_CMD="python3.13"
    PIP_CMD="pip3.13"
else
    echo "❌ Unsupported distribution: $DISTRO"
    echo "Consider compiling python from the source"
    echo "Check reference/install-python-from-source.txt"
    exit 1
fi

# Verify installation
echo "🔎 Verifying Python installation..."
if command -v $PYTHON_CMD >/dev/null 2>&1; then
    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo "✅ $PYTHON_VERSION installed."
else
    echo "❌ $PYTHON_CMD installation failed."
    exit 1
fi

if command -v $PIP_CMD >/dev/null 2>&1; then
    PIP_VERSION=$($PIP_CMD --version)
    echo "✅ $PIP_VERSION installed."
else
    echo "❌ $PIP_CMD installation failed."
    exit 1
fi

echo "✅ Python 3.13 installation complete!"
