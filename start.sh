#!/bin/bash
# Make sure this script is executable (chmod +x start.sh)

# Verify environment
echo "Python version: $(python --version)"
echo "Gunicorn version: $(gunicorn --version || echo 'NOT FOUND')"
echo "Working directory: $(pwd)"
echo "Files: $(ls -la)"

# Start the application
if command -v gunicorn &> /dev/null; then
    echo "Starting with Gunicorn..."
    gunicorn wsgi:app
else
    echo "Gunicorn not found, using Flask development server..."
    python wsgi.py
fi