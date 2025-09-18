# AtmosInsight

An AWS-native, living atlas of the atmosphere and near-space. AtmosInsight aggregates real-time and recent historical signals—severe-weather alerts, radar, GOES satellite imagery, lightning, fire detections, air quality, hydrologic/ocean data, and space-weather indicators—into a trusted, fast experience.

## 🌟 Features

- **Real-time Weather Data**: NEXRAD radar, GOES satellite, MRMS national mosaic, NWS alerts
- **Interactive Mapping**: MapLibre GL JS with PMTiles basemap and CyclOSM styling
- **Time Animation**: 5 FPS playback with temporal joining and stale data detection
- **Production Ready**: Container-based Lambda services with full CI/CD automation
- **Cost Optimized**: Designed for ≤$30/month at hobby scale with S3 lifecycle policies

## 🏗️ Architecture

- **Frontend**: Vite + React + MapLibre GL JS + CyclOSM basemap via PMTiles
- **Backend**: AWS Lambda containers + API Gateway + S3 + CloudFront + EventBridge
- **Data Processing**: TiTiler for raster tiles, Py-ART for radar, xarray for GOES/MRMS
- **Infrastructure**: Terraform for AWS resource management
- **CI/CD**: GitHub Actions with automated deployments

## 📊 Data Layers

### NEXRAD Level II Radar (Priority #1)
- **Source**: NOAA Level II from `noaa-nexrad-level2` S3 bucket
- **Processing**: Py-ART with polar-to-Cartesian gridding using Barnes weighting
- **Coverage**: 240km radius per site, 1km resolution
- **Updates**: On-demand via `/radar/prepare` API

### MRMS National Mosaic (Priority #2)  
- **Source**: MergedReflectivityQComposite from `noaa-mrms-pds` S3 bucket
- **Processing**: GRIB2 → xarray → CONUS reprojection at 2.5km resolution
- **Coverage**: Continental United States
- **Updates**: Automated every 5 minutes via EventBridge

### GOES-16 ABI Band 13 (Priority #3)
- **Source**: ABI Level 1b Radiance from `noaa-goes16` S3 bucket  
- **Processing**: Radiance → brightness temperature → geographic projection
- **Coverage**: CONUS sector with geostationary correction
- **Updates**: Every 10 minutes, on-demand via `/goes/prepare` API

### NWS Alerts
- **Source**: `api.weather.gov/alerts/active` REST API
- **Processing**: GeoJSON → Mapbox Vector Tiles via Tippecanoe
- **Coverage**: CONUS + Alaska + Hawaii + marine zones
- **Updates**: Automated every 5 minutes

## 🚀 Quick Start

> **Local rebuild in progress:** See `local/README.md` for the new local-first architecture. The root stack described below reflects the original AWS-oriented implementation and remains for reference until the migration completes.

### Prerequisites

```bash
# Required versions
Node.js 20 (see .nvmrc)
Python 3.11 (see .python-version)  
Docker (for container builds)
Terraform >= 1.5
AWS CLI v2
```

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install AWS CLI (if not already installed)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret, and region (us-east-1)
```

### 2. Set Up ECR Repositories

```bash
# Create ECR repositories for Lambda container images
./scripts/deploy/setup-ecr.sh us-east-1

# Output will show repository URIs like:
# 123456789012.dkr.ecr.us-east-1.amazonaws.com/atmosinsight-tiler
```

### 3. Build and Push Container Images

```bash
# Build all Lambda containers and push to ECR
./scripts/deploy/build-and-push-containers.sh us-east-1

# This builds:
# - atmosinsight-tiler (TiTiler for raster tiles)
# - atmosinsight-radar-prepare (NEXRAD Level II processing)
# - atmosinsight-goes-prepare (GOES ABI processing)  
# - atmosinsight-mrms-prepare (MRMS GRIB2 processing)
# - atmosinsight-alerts-bake (NWS alerts MVT generation)
```

### 4. Deploy Infrastructure

```bash
# Initialize and deploy Terraform infrastructure
cd infra/terraform
terraform init
terraform plan -var-file=env/us-east-1.tfvars
terraform apply -auto-approve

# Get outputs for next step
STATIC_BUCKET=$(terraform output -raw static_bucket_name)
DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)
echo "Static Bucket: $STATIC_BUCKET"
echo "Distribution ID: $DISTRIBUTION_ID"
```

### 5. Deploy Frontend and Static Assets

```bash
# Return to root directory
cd ../..

# Build and deploy frontend
npm run build
./scripts/deploy/upload-static.sh "$STATIC_BUCKET" "$DISTRIBUTION_ID"

# Upload your planet.z15.pmtiles file to web-static/basemaps/ first
# aws s3 cp your-planet.z15.pmtiles s3://$STATIC_BUCKET/basemaps/planet.z15.pmtiles
```

### 6. Configure DNS (One-time setup)

In your Cloudflare dashboard for `westfam.media`:
1. Go to DNS settings
2. Add NS record:
   - **Name**: `weather`  
   - **Type**: `NS`
   - **Value**: Use the 4 name servers from `terraform output route53_name_servers`
   - **Proxy status**: DNS only (gray cloud)

### 7. Verify Deployment

```bash
# Check health endpoint
curl https://weather.westfam.media/healthz | jq

# Visit the application
open https://weather.westfam.media

# Check status page
open https://weather.westfam.media/status.html
```

## 🔄 GitHub Actions CI/CD

### Setup Automated Deployments

1. **Add GitHub Secrets** in your repository settings:
   ```
   AWS_ACCESS_KEY_ID: Your AWS access key
   AWS_SECRET_ACCESS_KEY: Your AWS secret key
   ```

2. **Workflow Triggers**:
   - **Push to main**: Full deployment pipeline
   - **Pull request**: Build and test only
   - **Manual dispatch**: On-demand deployments

3. **Pipeline Steps**:
   ```yaml
   ✅ Test and build frontend
   ✅ Build and push container images to ECR
   ✅ Deploy infrastructure with Terraform
   ✅ Upload static assets to S3  
   ✅ Invalidate CloudFront cache
   ✅ Health check validation
   ✅ Deployment notifications
   ```

## 🛠️ Local Development

### Frontend Development

```bash
# Start development server with hot reload
npm run dev

# Access at http://localhost:3000
# Configure local API endpoints in web/.env
```

### API Development  

```bash
# Build specific Lambda container locally
cd services/radar-prepare
docker build -t radar-prepare .

# Test container (requires AWS credentials)
docker run -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY radar-prepare
```

### Database

The application uses S3-based indices by default. Optional DynamoDB can be enabled by setting `enable_dynamo = true` in `infra/terraform/env/us-east-1.tfvars`.

## 📊 Performance Targets

- **Tile Fetch**: p95 ≤ 600ms from CloudFront edge
- **Initial Load**: p95 ≤ 3s for first paint
- **Availability**: 99.5% monthly with graceful degradation
- **Cost**: ≤ $30/month at 5-10K requests/month

## 📁 Project Structure

```
atmosinsight/
├── README.md                    # This file
├── package.json                 # Root npm configuration
├── .github/workflows/           # GitHub Actions CI/CD
├── web/                        # React frontend
│   ├── src/components/         # MapLibre components
│   ├── src/store/             # Zustand state management
│   └── src/lib/               # Time utilities and API client
├── web-static/                # Static assets served from S3
│   ├── styles/cyclosm.json    # CyclOSM MapLibre style
│   ├── sprites/cyclosm/       # Map sprites
│   ├── fonts/                 # SDF glyphs  
│   └── basemaps/              # PMTiles files
├── services/                  # Lambda container services
│   ├── tiler/                # TiTiler for raster tiles
│   ├── radar-prepare/        # NEXRAD Level II → COG
│   ├── goes-prepare/         # GOES ABI → COG
│   ├── mrms-prepare/         # MRMS GRIB2 → COG
│   ├── alerts-bake/          # NWS alerts → MVT
│   └── healthz/              # Health check endpoint
├── infra/terraform/          # Infrastructure as Code
│   ├── modules/              # Reusable Terraform modules
│   └── env/                  # Environment configurations
├── scripts/deploy/           # Deployment automation
└── ops/monitoring/           # Observability configuration
```

## 🗂️ API Endpoints

### Health & Status
- `GET /healthz` - System health with data freshness
- `GET /status.html` - Public status page

### Data Preparation (Manual Triggers)
- `POST /radar/prepare?site=KTLX&time=2024-12-01T18:00:00Z`
- `POST /goes/prepare?band=13&sector=CONUS&time=latest`  
- `POST /mosaic/prepare?product=reflq&time=latest`

### Tile Serving (Automatic via TiTiler)
- `GET /tiles/weather/goes-c13/{timestamp}/kelvin/{z}/{x}/{y}.png`
- `GET /tiles/weather/mrms-reflq/{timestamp}/{z}/{x}/{y}.png`
- `GET /tiles/weather/nexrad-{site}/{timestamp}/{z}/{x}/{y}.png`

### Timeline Data
- `GET /goes/timeline?band=13&sector=CONUS&limit=12`
- `GET /mosaic/timeline?product=reflq&limit=12`
- `GET /indices/alerts/index.json`

## 🚨 Monitoring & Alerts

### CloudWatch Dashboards
- Lambda function durations and errors
- API Gateway 4XX/5XX error rates
- CloudFront request metrics
- Cost monitoring with budget alerts

### Health Checks
- Automated probes of S3 read/write
- Data freshness monitoring (>10 min = stale)
- TiTiler latency measurements

### Budget Monitoring
- AWS Budget alerts at $20/$25/$30 monthly
- Cost breakdown by service
- Usage forecasting

## 🔧 Troubleshooting

### Common Issues

**Container build failures:**
```bash
# Check Docker daemon is running
docker info

# Login to ECR manually
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

**Terraform deployment errors:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Destroy and recreate if needed
terraform destroy -var-file=env/us-east-1.tfvars
```

**Frontend build issues:**
```bash
# Clear cache and reinstall
rm -rf web/node_modules web/dist
npm install
npm run build
```

### Log Analysis

```bash
# View Lambda logs
aws logs tail /aws/lambda/atmosinsight-healthz --follow

# Check API Gateway logs
aws logs describe-log-groups --log-group-name-prefix "API-Gateway-Execution"

# Monitor S3 access logs
aws logs tail atmosinsight-cloudfront-logs --follow
```

## 📝 License & Attribution

- **Code**: MIT License
- **Basemap**: © OpenStreetMap contributors (ODbL) 
- **Style**: © CyclOSM (CC-BY-SA 2.0)
- **Data**: NOAA/NWS (Public Domain)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Use GitHub Issues for bugs and feature requests  
- **Health**: Monitor `/healthz` endpoint and `/status.html` page
- **Logs**: CloudWatch logs for all Lambda functions

---

**🎯 Production Deployment Checklist:**
- [ ] AWS CLI installed and configured
- [ ] ECR repositories created  
- [ ] Container images built and pushed
- [ ] Terraform infrastructure deployed
- [ ] DNS configured in Cloudflare
- [ ] Frontend and PMTiles uploaded
- [ ] Health check passing
- [ ] GitHub Actions configured
- [ ] Budget alerts configured

**Application URL**: https://weather.westfam.media  
**Status Page**: https://weather.westfam.media/status.html
