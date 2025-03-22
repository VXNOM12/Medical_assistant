FROM python:3.9-slim

WORKDIR /app

# Install pre-built packages
RUN pip install --no-cache-dir flask gunicorn transformers torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# Copy your application code
COPY . .

# Expose port
EXPOSE 10000

# Command to run the application
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:10000"]