# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies required for radar/gdal stack
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gdal-bin \
        libgdal-dev \
        libhdf5-dev \
        libnetcdf-dev \
        libproj-dev \
        proj-bin \
        libgeos-dev \
        libjpeg-turbo-progs \
    libtiff6 \
        libopenjp2-7 \
        libpng-dev \
        libfreetype6 \
        libexpat1 \
        git \
        curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_CONFIG=/usr/bin/gdal-config

# Install Python dependencies
RUN mkdir -p /services/radar-prepare /services/goes-prepare
COPY services/radar-prepare/requirements.txt /services/radar-prepare/requirements.txt
COPY local/services/ingestion/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application source and shared legacy radar module
COPY services/radar-prepare /app/services/radar-prepare
COPY services/goes-prepare /app/services/goes-prepare
COPY local/services/ingestion/src /app/local/services/ingestion/src

ENV PYTHONPATH=/app

EXPOSE 8084
CMD ["uvicorn", "local.services.ingestion.src.main:app", "--host", "0.0.0.0", "--port", "8084"]
