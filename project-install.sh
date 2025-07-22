#!/bin/bash

set -e  # Exit on first error


# Load ENVIRONMENT from .env if present
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Determine virtualenv path
if [ "$ENVIRONMENT" == "development" ]; then
    VENV_PATH="venv"
else
    VENV_PATH="$HOME/.virtualenvs/movieframe"
fi

# Create virtual environment if not exists
if [ ! -d "$VENV_PATH" ]; then
    echo "🐍 Creating virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtualenv
echo "✅ Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

echo "✅ Python dependencies installed."
echo "🚀 Setup complete. You can now run movieplayer.py"
