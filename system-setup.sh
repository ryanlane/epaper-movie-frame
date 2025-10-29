#!/bin/bash

set -e

echo "🔧 Updating APT and installing system-level dependencies..."
sudo apt update
sudo apt install -y python3-venv python3-pip python3-opencv libgl1 libatlas-base-dev libopenjp2-7 libtiff5 python3-dev

echo "✅ System dependencies installed."
