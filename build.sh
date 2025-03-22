#!/usr/bin/env bash
# Install system dependencies needed for numpy, scipy, etc.
apt-get update
apt-get install -y build-essential gfortran libopenblas-dev

# Continue with the normal build process
pip install -r requirements.txt
