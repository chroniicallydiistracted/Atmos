# syntax=docker/dockerfile:1
FROM ghcr.io/developmentseed/titiler:latest

# Install additional dependencies for AtmosInsight
RUN pip install --no-cache-dir \
    rio-cogeo \
    boto3

# Copy custom TiTiler configuration
COPY app.py /app/app.py

# Set Lambda handler
CMD ["app.handler"]