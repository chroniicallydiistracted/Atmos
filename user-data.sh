#!/bin/bash
yum update -y
yum install -y awscli htop

wget https://github.com/protomaps/go-pmtiles/releases/latest/download/pmtiles-linux-arm64
chmod +x pmtiles-linux-arm64
mv pmtiles-linux-arm64 /usr/local/bin/pmtiles

mkfs.ext4 /dev/nvme1n1
mkdir /data
mount /dev/nvme1n1 /data
chmod 777 /data
