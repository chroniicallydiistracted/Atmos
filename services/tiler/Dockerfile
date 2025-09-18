# syntax=docker/dockerfile:1
FROM ghcr.io/developmentseed/titiler:latest

# No AWS dependencies; base image already includes FastAPI, rio-tiler, etc.
# Install any extra libs if needed (kept minimal)
RUN pip install --no-cache-dir rio-cogeo minio

WORKDIR /app

# Copy custom TiTiler application
COPY server.py /app/server.py

# Run as standard ASGI app
ENV PORT=8083
EXPOSE 8083
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8083"]
