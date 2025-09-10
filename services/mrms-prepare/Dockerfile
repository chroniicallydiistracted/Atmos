# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for GRIB2 processing
RUN yum update -y && \
    yum install -y \
        gcc \
        gcc-c++ \
        gdal \
        gdal-devel \
        proj \
        proj-devel \
        grib_api \
        grib_api-devel \
        eccodes \
        eccodes-devel \
        netcdf \
        netcdf-devel \
        hdf5 \
        hdf5-devel \
        zlib-devel && \
    yum clean all

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY handler.py ./

CMD ["handler.lambda_handler"]