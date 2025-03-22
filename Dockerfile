FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Create required directories
RUN mkdir -p /app/data /app/logs /app/models /app/static /app/templates

# Expose port
EXPOSE 8000

# Run the application with Gunicorn
CMD gunicorn --workers=2 --bind=0.0.0.0:$PORT app:app