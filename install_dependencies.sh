#!/bin/bash

set -e  # Exit on first error

# Update and install OS packages
echo "🔧 Updating APT and installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-opencv python3-pip python3-venv

# Create a virtual environment if not present
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install inky[rpi,example-depends] \
            python-dotenv numpy Pillow \
            fastapi "uvicorn[standard]" \
            python-multipart sqlalchemy jinja2

echo "✅ All dependencies installed."

# Optional: Save to requirements.txt
pip freeze > requirements.txt
echo "📄 Requirements saved to requirements.txt"
echo "🚀 Setup complete. You can now run your FastAPI application."