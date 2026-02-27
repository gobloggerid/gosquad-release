#!/bin/bash
set -euo pipefail

# Update package information
sudo apt update && sudo apt upgrade -y

# Install software properties common
sudo apt install software-properties-common -y

# Install Python 3.13
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.13-dev python3.13-venv python3-pip
