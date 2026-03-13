#!/bin/bash
set -euo pipefail

echo "Installing python...."
sleep 2
echo ""

sudo apt update -y
sudo apt install software-properties-common -y
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.13-dev python3.13-venv python3-pip

echo "✅ Done installing python."
echo "Please run the next step!"