#!/usr/bin/env bash
<<<<<<< Updated upstream
# Install system dependencies needed for numpy, scipy, etc.
apt-get update
apt-get install -y build-essential gfortran libopenblas-dev

# Continue with the normal build process
pip install -r requirements.txt
=======
echo "Installing system dependencies for scientific Python packages..."

# Update package lists
apt-get update -y

# Install essential build tools and scientific computing dependencies
apt-get install -y build-essential gfortran libopenblas-dev liblapack-dev pkg-config

# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Force binary-only installation for problematic packages
pip install --only-binary=numpy,scipy numpy scipy

# Install the rest of the requirements
pip install -r requirements.txt
>>>>>>> Stashed changes
