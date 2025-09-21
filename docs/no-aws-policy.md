# No-AWS Policy (Local-First)

We will not utilize AWS services or SDKs. All components must run locally or use local-compatible interfaces.

## Forbidden (non-exhaustive)
- AWS services: S3, Lambda, ECR, ECS, Route 53, CloudFront, API Gateway, EventBridge, DynamoDB, CloudWatch, IAM, etc.
- SDKs/adapters: `boto3`, `botocore`, `aws-sdk` (Node), `Mangum` (Lambda adapters), and any AWS-specific middleware.

## Allowed Alternatives
- Object storage: MinIO (S3-compatible) using native MinIO SDKs (`minio` for Python, `minio` for Node).
- HTTP ingress: Caddy reverse proxy.
- Containers: Docker Compose for orchestration.
- Database: Postgres/PostGIS.
- Queues/scheduling: APScheduler / Cron inside containers.
- Tile serving: TiTiler (ASGI) or Mapnik-based servers running as local services (no Lambda wrappers).

## Coding Guidelines
- Do not import AWS SDKs. Use MinIO SDK and configure via `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`.
- Do not reference `s3://` URLs in code. Use bucket + key with MinIO client, or local filesystem paths.
- No Lambda handlers; expose HTTP servers directly (Uvicorn/Gunicorn).
- Keep configuration in `local/config/.env`; never use cloud credentials.

## Migration Notes
- Legacy services referencing AWS will be refactored incrementally to MinIO and local processes.
- Infra directories for Terraform/AWS remain for historical reference but are not used moving forward.
