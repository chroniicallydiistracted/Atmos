# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir rio-tiler fastapi uvicorn "titiler.application>=0.11.0" rio-cogeo minio

WORKDIR /app

# Copy custom TiTiler application
COPY server.py /app/server.py

# Run as standard ASGI app
ENV PORT=8083
EXPOSE 8083
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8083"]
