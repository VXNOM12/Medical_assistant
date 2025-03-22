#!/bin/bash
# Install core dependencies first
pip install --no-cache-dir -r requirements.txt

# Install PyTorch CPU version if needed (skip if already installed)
if ! pip show torch | grep -q "cpu"; then
    pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu
fi

# Verify gunicorn installation
which gunicorn || echo "WARNING: Gunicorn not found!"

# Print installed packages for debugging
pip list