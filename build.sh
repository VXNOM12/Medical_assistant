#!/bin/bash
# Install Python 3.9 if needed
echo "Installing dependencies with Python 3.9..."

# Install requirements
pip install --no-cache-dir -r requirements.txt

# Install CPU-only PyTorch separately
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu

# Print installed packages for debugging
pip list