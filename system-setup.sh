#!/bin/bash
echo "Updating package list..."
sudo apt update

echo "Installing required system packages..."
sudo apt install -y python3-dev python3-venv python3-pip libatlas-base-dev libopenjp2-7 libtiff5 libgl1

echo "System dependencies installed."
