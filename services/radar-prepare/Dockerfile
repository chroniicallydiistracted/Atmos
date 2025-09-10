# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for radar processing
RUN yum update -y && \
    yum install -y \
        gcc \
        gcc-c++ \
        gcc-gfortran \
        gdal \
        gdal-devel \
        proj \
        proj-devel \
        hdf5 \
        hdf5-devel \
        netcdf \
        netcdf-devel \
        zlib-devel \
        bzip2-devel && \
    yum clean all

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY handler.py ./

CMD ["handler.lambda_handler"]