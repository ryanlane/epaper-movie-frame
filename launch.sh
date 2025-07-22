#!/bin/bash

# Load ENVIRONMENT from .env if present
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Determine virtualenv path
if [ "$ENVIRONMENT" == "development" ]; then
    VENV_PATH="./venv"
else
    VENV_PATH="$HOME/.virtualenvs/movieframe"
fi

if [ ! -d "$VENV_PATH" ]; then
  echo "❌ Virtual environment not found at $VENV_PATH"
  echo "💡 Run './project-install.sh' to set it up first."
  exit 1
fi

echo "✅ Activating virtual environment..."
source "$VENV_PATH/bin/activate"

echo "🚀 Launching movieplayer..."
python movieplayer.py
