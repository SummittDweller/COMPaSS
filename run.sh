#!/usr/bin/env bash
# COMPaSS - Cache Owner Management Platform and Sites System - Quick Launch Script
# Sets up a Python virtual environment and launches the Flet app.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== COMPaSS — Cache Owner Management Platform and Sites System ==="
echo

PYTHON_CMD="python3"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    echo "✓ Virtual environment created"
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo

# Install / upgrade dependencies
echo "Installing dependencies..."
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r python_requirements.txt --quiet
echo "✓ Dependencies installed"
echo

# Launch the app
echo "Launching COMPaSS..."
echo
.venv/bin/python app.py
