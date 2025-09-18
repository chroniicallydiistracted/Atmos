# AWS Resource Inventory

This inventory captures every AWS resource currently referenced by the AtmosInsight repository. Use it to plan the migration to local infrastructure and to ensure all cloud dependencies are retired.

## Storage Services
- **S3 Buckets (Terraform `modules/static_site` & `glacier.tf`)**
  - `atmosinsight-static-<suffix>` – hosts SPA build, PMTiles, styles, sprites, fonts. Public access blocked; served via CloudFront.
  - `atmosinsight-derived-<suffix>` – stores derived weather datasets (GOES, MRMS, NEXRAD tiles) with lifecycle policies (7-day expiry and Glacier archiving after 90+ days).
  - `atmosinsight-glacier-metadata` – retains Glacier retrieval metadata with versioning and SSE.
  - Lifecycle rules include transitions to `STANDARD_IA`, `GLACIER`, `DEEP_ARCHIVE`, and aggressive cleanup for `tmp/` and `logs/` prefixes.
- **NOAA Open Data Buckets (Lambda IAM policy)** – Read-only access granted to `noaa-goes16`, `noaa-nexrad-level2`, `noaa-mrms-pds` for ingest Lambdas.
- **Font Uploads (`scripts/upload_fonts_to_s3.sh`)** – Syncs `.pbf` glyphs to a user-specified S3 prefix.

## Compute & Container Services
- **AWS Lambda Functions (Terraform `modules/api_gw_lambda`, `alerting.tf`, `glacier.tf`)**
  - Core API/Data pipeline: `atmosinsight-healthz`, `atmosinsight-tiler`, `atmosinsight-radar-prepare`, `atmosinsight-goes-prepare`, `atmosinsight-mrms-prepare`, `atmosinsight-alerts-bake`.
  - Aux/alerting: `atmosinsight-discord-notifier`, `atmosinsight-sms-notifier`, `atmosinsight-glacier-retrieval`.
- **AWS Lambda Packaging** – Current Terraform references ZIP artifacts under `services/healthz/healthz.zip` and placeholder zips for other functions.
- **Amazon ECR (scripted)** – Repositories expected for containerized Lambdas: `atmosinsight-tiler`, `-radar-prepare`, `-goes-prepare`, `-mrms-prepare`, `-alerts-bake` (`scripts/deploy/setup-ecr.sh`).

## Networking & Delivery
- **Amazon CloudFront** – Primary distribution serving SPA, PMTiles, styles. Includes behaviors for `/basemaps/*`, `/styles/*`, `/sprites/*`, `/fonts/*`, `/tiles/*`, `/status.html`, `/healthz`.
- **Amazon Route 53** – Optional hosted zone for `weather.westfam.media` with ACM DNS validation records.
- **AWS Certificate Manager** – Wildcard certificate for `*.weather.westfam.media` when `acm_certificate_arn` not provided.
- **Amazon API Gateway (HTTP API)** – `atmosinsight-api` with CORS for CloudFront + localhost, throttling (`rate=5`, `burst=10`), routes for `/healthz`, `/tiles/*`, `/radar/*`, `/goes/*`, `/mosaic/*`, `/alerts/*`, `/indices/*` pointing to corresponding Lambda integrations.
- **VPC Module (`modules/network`)** – Defines VPC, public/private subnets, IGW, NAT Gateway, route tables. Not wired in `main.tf` but available for ECS/RDS extension.

## Scheduling, Messaging, and Notifications
- **Amazon EventBridge** – Rules `atmosinsight-mrms-schedule` and `atmosinsight-alerts-schedule` trigger MRMS and alerts Lambdas every 5 minutes.
- **AWS Lambda Permissions** – EventBridge invoke permissions for MRMS/alerts Lambdas.
- **Amazon SNS** – Topic `atmosinsight-alerts` for notifications.
- **CloudWatch Events/Lambda Subscriptions** – SNS subscriptions invoking Discord and SMS notifier Lambdas.

## Databases & Caching
- **Amazon DynamoDB (optional)** – Module `modules/dynamo` provisioned when `enable_dynamo = true` (not enabled in tfvars). Would support indices/caching if activated.

## Monitoring & Logging
- **Amazon CloudWatch Log Groups** – `/aws/lambda/atmosinsight-*` with 14-day retention for core Lambdas.
- **CloudWatch Metric Alarms** – Lambda error alarms per function, API Gateway 4XX alarm, custom `AtmosInsight/DataFreshness` metric alarm.
- **AWS Budgets** – Monthly cost budget (`limit $30`) with email notifications.

## Identity & Access Management
- **IAM Roles & Policies**
  - `atmosinsight-lambda-role` with policies for CloudWatch Logs and S3 (static, derived, NOAA buckets).
  - Roles for Discord notifier, SMS notifier, Glacier retrieval (each with AWSLambdaBasicExecutionRole or custom policies).
- **Lambda Permissions** – Grants for SNS/EventBridge to invoke corresponding Lambdas.

## Miscellaneous
- **AWS CloudFormation/Terraform Backend** – Terraform state currently stored locally (`infra/terraform/terraform.tfstate`), no remote backend configured.
- **S3 Lifecycle Extensions** – Glacier archival rules for derived data (90/365 days) and deletion after ~7 years.
- **Deployment Tooling** – Bash scripts rely on AWS CLI for S3 sync, ECR operations, CloudFront invalidations, Terraform deploys.

---

Use this inventory to map each AWS dependency to its replacement during the migration process.
