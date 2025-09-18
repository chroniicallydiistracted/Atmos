# AtmosInsight Local Migration Plan

This runbook enumerates every required step to migrate AtmosInsight from AWS-managed infrastructure to a self-hosted, local-first environment. Execute phases in order; do not proceed to a later phase until acceptance criteria in the current phase are met.

## Phase 0 – Discovery and Readiness
- [x] Inventory all AWS resources (S3 buckets, Lambda functions, API Gateway stages, CloudFront distributions, RDS instances, Route53 zones, IAM roles/policies, CloudWatch alarms, EventBridge rules, ECR repos, SSM parameters). Export to YAML/JSON snapshots for reference. (See `docs/aws-inventory.md`)
- [x] Capture credentials/keys currently stored in AWS Secrets Manager or SSM Parameter Store. Plan a secure replacement (local secret manager or offline vault). (See `docs/secret-migration.md`)
- [x] Audit data retention/compliance constraints; confirm on-prem storage and backups satisfy legal + business requirements. (See `docs/data-compliance-check.md`)
- [ ] Verify local hardware capacity: ≥24 cores, 96 GB RAM, 1 TB NVMe primary, 2 TB secondary/NAS, redundant power, monitored cooling.
- [ ] Establish source-of-truth documentation repository (this repo) and incident response contacts for local operations.

## Phase 1 – Core Infrastructure Stand-up (Local)
- [ ] Install and harden base OS on local host(s); apply updates, configure firewall (allow only required inbound ports), enable auditing.
- [ ] Provision virtualization/containers (Docker Engine + Compose/Podman, or Kubernetes if required). Decide single-node vs. small cluster.
- [ ] Deploy internal certificate authority or configure ACME client (e.g., `certbot`, `caddy`) for TLS certificate automation.
- [ ] Set up reverse proxy/load balancer (Caddy, Traefik, or Nginx) with HTTPS termination, HTTP/2, logging, and rate limiting.
- [ ] Install identity and access management tooling (e.g., Keycloak or simple LDAP) if multi-user access is required.
- [ ] Stand up local object storage (MinIO or Ceph RGW) with S3-compatible API. Create buckets: `raw`, `derived`, `tiles`, `logs`.
- [ ] Initialize monitoring and alerting stack (Prometheus, Grafana, Loki/ELK) pointed at local hosts.
- [ ] Configure backup target (external NAS or offline disks). Define snapshot schedule for Postgres, object store, configs.

## Phase 2 – Data Ingestion Pipeline Refactor
- [ ] Implement shared FetchWithRetry helper for backend services to download NOAA/other public data over HTTPS.
- [ ] Update GOES, MRMS, and NEXRAD prepare handlers to write to filesystem/MinIO instead of AWS S3 (configurable root path or endpoint).
- [ ] Replace boto3 dependencies where no longer required; if S3 API still used, point to MinIO endpoint and local credentials.
- [ ] Adjust environment variable schema (e.g., `DERIVED_BUCKET_NAME` → `DERIVED_ROOT_PATH` or `OBJECT_STORE_ENDPOINT`).
- [ ] Ensure Tippecanoe outputs and indices are stored locally; compress TileJSON files explicitly prior to flagging gzip encoding.
- [ ] Build automated integrity checks (checksums, timestamp validation) for ingested files stored under `data/raw`.
- [ ] Validate each service end-to-end locally: trigger `goes-prepare`, `mrms-prepare`, `radar-prepare`, `alerts-bake` and confirm outputs appear under the new storage path.

## Phase 3 – Basemap and Vector Assets Localization
- [ ] Download Geofabrik extracts, Natural Earth layers, land/water polygons, and DEM tiles into `data/raw/vector`.
- [ ] Update importer scripts (`services/cyclosm/importer`) to read from local files rather than remote HTTP downloads where possible.
- [ ] Stand up local Postgres + PostGIS (Docker or bare metal). Configure volumes per storage layout plan.
- [ ] Run osm2pgsql import locally; monitor resource usage; document tuning parameters.
- [ ] Generate hillshade/contours with GDAL locally; store results under `data/derived/cyclosm`.
- [ ] Modify CyclOSM renderer startup to skip AWS font sync; mount fonts from repository `fonts/` into container.
- [ ] Implement S3 cache abstraction in renderer to target MinIO/local filesystem; verify metatile rendering works against Postgres.

## Phase 4 – Application Layer Updates
- [ ] Repoint TiTiler (`services/tiler/app.py`) to read tiles from local object store or filesystem; implement Kelvin→Celsius/Fahrenheit conversions.
- [ ] Update Healthz Lambda replacement to perform real probes (filesystem/object-store writes, renderer HTTP checks) without AWS dependencies.
- [ ] Adjust frontend configuration defaults (`VITE_API_BASE`, `VITE_TILE_BASE`, style URLs) to use local domain endpoints.
- [ ] Replace AWS-specific deployment scripts with local equivalents (Docker Compose, Ansible, or Make targets).
- [ ] Remove AWS SDK dependencies from services where no longer needed; clean `package.json`/`requirements.txt`.
- [ ] Set up CI/CD (local Git hooks or self-hosted runner) to build/test containers before deploying to on-prem hosts.

## Phase 5 – Domain & Networking Migration
- [ ] Transfer DNS management from Route 53 to Cloudflare (if not already using). Import existing records for historic reference.
- [ ] Design new DNS architecture: `app`, `api`, `tiles`, `basemap`, `status` subdomains pointing to public IP of reverse proxy.
- [ ] Configure Cloudflare SSL/TLS (Full Strict) with certificates installed on local proxy. Optionally enable Cloudflare proxying for DDoS mitigation.
- [ ] Implement split-horizon DNS if internal clients should resolve to private IPs.
- [ ] Update application configs and public documentation with new URLs.
- [ ] Decommission AWS Route 53 hosted zone after verifying all records resolve correctly via Cloudflare.

## Phase 6 – Security Hardening
- [ ] Implement firewall rules restricting ingress to HTTPS, SSH (with key auth), and VPN ports; block unused services.
- [ ] Enforce TLS for all internal services via reverse proxy or service mesh.
- [ ] Set up centralized secret storage (HashiCorp Vault, Doppler, or encrypted `.env` files) and rotate keys migrated from AWS Secrets Manager.
- [ ] Configure log forwarding to SIEM/monitoring stack; enable alerting on anomalies.
- [ ] Conduct vulnerability scans on containers/hosts (Trivy, Lynis). Document remediation steps.
- [ ] Establish backup and disaster recovery runbooks; test restoration from snapshots.

## Phase 7 – Testing & Validation
- [ ] Build automated test suite to exercise ingest, processing, tile serving, API endpoints, and frontend behavior against local stack.
- [ ] Run load tests on TiTiler and CyclOSM renderer to ensure hardware meets performance targets.
- [ ] Validate data freshness alerts (no stale data indicators) using the new health checks.
- [ ] Conduct failover drills (simulate hardware failure, restore from backup, DNS cutover).
- [ ] Gather stakeholder sign-off on feature parity and performance.

## Phase 8 – Cutover & Decommission
- [ ] Schedule production cutover window; announce maintenance period if needed.
- [ ] Freeze AWS-side pipelines; ensure final dataset sync to local store completes successfully.
- [ ] Update DNS TTL to minimal value; switch A/AAAA records to new on-prem IPs.
- [ ] Monitor logs, metrics, and user feedback for 48 hours; address issues immediately.
- [ ] After stabilization, revoke AWS IAM credentials, shut down Lambdas/ECS, and snapshot/destroy remaining AWS resources for archival.
- [ ] Update billing/finance records to reflect AWS decommissioning.
- [ ] Document lessons learned and update runbooks for ongoing local operations.

---

**Appendices**
- A. Storage layout reference (see `docs/migration-off-aws.md` & `docs/cyclosm-raster-plan.md`).
- B. Hardware BOM and warranty contacts.
- C. Monitoring dashboard URLs and alert escalation matrix.
