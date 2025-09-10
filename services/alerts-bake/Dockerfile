# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.11

# Install tippecanoe for MVT generation
RUN yum update -y && \
    yum groupinstall -y "Development Tools" && \
    yum install -y git sqlite-devel zlib-devel && \
    git clone https://github.com/felt/tippecanoe.git && \
    cd tippecanoe && \
    make -j$(nproc) && \
    make install && \
    cd .. && \
    rm -rf tippecanoe && \
    yum remove -y git "Development Tools" && \
    yum clean all

# Install Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

# Copy handler
COPY handler.py ./

CMD ["handler.lambda_handler"]