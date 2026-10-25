#!/bin/bash
# Cross-platform launch script for macOS and Linux

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the script's directory
cd "$(dirname "$0")"

VENV_DIR="KittyAI/.venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "=== Creating Virtual Environment ==="
    python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Ensure pip is present
python3 -m ensurepip --default-pip --upgrade

# Install/update dependencies
echo "=== Installing/Updating Dependencies ==="
python3 -m pip install --upgrade pip
pip install -r KittyAI/requirements.txt

# Launch Kitty AI
echo "=== Starting Kitty AI Companion ==="
python KittyAI/main.py
