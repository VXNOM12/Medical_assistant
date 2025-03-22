#!/usr/bin/env bash
echo "Installing system dependencies for scientific Python packages..."

# Update package lists
apt-get update -y

# Install essential build tools and scientific computing dependencies
apt-get install -y build-essential gcc g++ gfortran libopenblas-dev liblapack-dev pkg-config python3-dev

# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Force binary-only installation for scientific packages
pip install --only-binary=:all: numpy scipy pandas scikit-learn

# Install the rest of the requirements (excluding what we've already installed)
grep -v "numpy\|scipy\|pandas\|scikit-learn" requirements.txt | pip install -r /dev/stdin