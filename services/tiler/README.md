# TiTiler Lambda Service

TiTiler-based Lambda function for serving raster tiles from AtmosInsight COGs stored in S3.

## Features

- Serves PNG tiles from GOES, MRMS, and NEXRAD COGs
- Temperature unit conversions (Kelvin ↔ Celsius ↔ Fahrenheit)
- Custom rescaling and styling
- CORS support for AtmosInsight frontend
- CloudFront-compatible caching headers

## Endpoints

- `GET /tiles/weather/{dataset}/{timestamp}/{z}/{x}/{y}.png`
- `GET /healthz`

## Datasets

- `goes-c13`: GOES ABI Band 13 IR imagery
- `mrms-reflq`: MRMS composite reflectivity
- `nexrad-{SITE}`: Single-site NEXRAD reflectivity

## Query Parameters

- `style`: `kelvin`, `celsius`, `fahrenheit` (for GOES)
- `rescale`: Custom rescale range (e.g., `180,330`)

## Deployment

Built as a container image based on the official TiTiler Lambda image with AtmosInsight customizations.