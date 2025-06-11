#!/bin/bash

VENV_DIR="$HOME/.virtualenvs/movieframe"

if [ ! -d "$VENV_DIR" ]; then
  echo "❌ Virtual environment not found at $VENV_DIR"
  echo "💡 Run './project-install.sh' to set it up first."
  exit 1
fi

echo "✅ Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "🚀 Launching movieplayer..."
python movieplayer.py
