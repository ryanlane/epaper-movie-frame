#!/bin/bash

VENV_DIR="$HOME/.virtualenvs/movieframe"

echo "Creating virtual environment at $VENV_DIR..."
python3 -m venv "$VENV_DIR"

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "All Python dependencies installed."
