# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.11

# Install GDAL and other system dependencies
RUN yum update -y && \
    yum install -y gdal gdal-devel gcc g++ && \
    yum clean all

# Install Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

# Copy handler
COPY handler.py ./

CMD ["handler.lambda_handler"]