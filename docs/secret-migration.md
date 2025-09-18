# Credential & Secret Migration Plan

This document enumerates every credential referenced in the AtmosInsight stack, the current storage location (AWS or otherwise), and the plan for extracting and loading it into the new local secret store.

## 1. AWS-Managed Secrets
| Secret | Current Location | Consumers | Notes / Extraction | Local Replacement |
| --- | --- | --- | --- | --- |
| `atmos/cyclosm/db_password` (Secrets Manager) | AWS Secrets Manager (Terraform `services/cyclosm/iam.tf`) | CyclOSM importer & renderer ECS tasks (`PGPASSWORD`) | Run `aws secretsmanager get-secret-value --secret-id atmos/cyclosm/db_password` and record value securely. Rotate after migration. | Store in local Vault/Pass/1Password; inject into Postgres container via `.env` or Vault sidecar. |
| Derived/static bucket credentials | IAM user/role credentials used for deployments (AWS CLI, Terraform) | Deployment scripts (`aws s3 sync`, `aws ecr`, `terraform`) | Enumerate IAM access keys with `aws iam list-access-keys --user-name <user>`. Disable after migration. | Replace with local MinIO access key; store in local vault and `.env`. |
| Lambda execution role credentials | IAM roles (`atmosinsight-lambda-role`, notifier roles) | All AWS Lambdas | No discrete secret; document role policies for audit before removal. | Superseded by local service accounts. |

## 2. Application Environment Variables
| Variable | Where Defined | Purpose | Current Value Source | Migration Plan |
| --- | --- | --- | --- | --- |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | README instructions, Docker examples | Auth for AWS CLI / Lambda containers | IAM user secrets | Remove from runtime; use MinIO credentials for local tests. Store new creds in local secret manager. |
| `DERIVED_BUCKET_NAME`, `STATIC_BUCKET_NAME` | Lambda env (`modules/api_gw_lambda`) | S3 bucket names | Terraform-provisioned | Replace with filesystem/object-store paths; no secret required. |
| `PGPASSWORD` | Docker compose (`osmpassword`), Terraform secrets | Postgres auth | Hard-coded dev default; production stored in Secrets Manager | Rotate to strong password; store in local vault; update docker compose `.env`. |
| `DISCORD_WEBHOOK_URL` | Terraform variable (sensitive) | Alert notifications | Stored in Terraform variables/Cloud secrets | Export from TF vars or Secrets Manager; move to local alerting config (Grafana/Loki/ntfy) and remove from Terraform. |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_PHONE`, `ALERT_PHONE` | Terraform vars (sensitive) | SMS alerts | Stored inline or in tfvars | Retrieve from parameter storage (if used); migrate to local alerting stack or discontinue. |
| `CLOUDFLARE_API_TOKEN` (future) | Not in repo, but required for DNS automation | Manage DNS with Cloudflare | Stored in Cloudflare dashboard/API | Generate token with limited scope; store locally in vault; use with Terraform `cloudflare` provider or Ansible. |

## 3. Third-Party Credentials Outside AWS
| Provider | Credential | Current Handling | Migration Action |
| --- | --- | --- | --- |
| Cloudflare | Account login + API token (for DNS) | Managed externally | Rotate token prior to DNS cutover, store in vault. |
| GitHub/GitLab | Repo access tokens (if CI) | Not in repo | Ensure self-hosted runner has scoped deploy key. |
| Map/Tiles data sources | NOAA HTTP (no key) | Public | No change. |

## 4. Extraction Checklist
1. Log into AWS account used for AtmosInsight.
2. Run inventory commands:
   ```bash
   aws secretsmanager list-secrets
   aws ssm describe-parameters --parameter-filters Key=Path,Option=Contains,Values=atmos
   aws iam list-access-keys --user-name <deploy-user>
   ```
3. For each secret, export value (`aws secretsmanager get-secret-value ...`) and place into secure offline vault (1Password, Bitwarden, paper).
4. Record which services consume each secret and what new service will replace it locally.
5. Revoke AWS access keys immediately after confirming local replacements.

## 5. Local Secret Store Options
- **HashiCorp Vault (self-hosted)** – production-grade, supports dynamic credentials.
- **1Password/Bitwarden CLI** – simple storage + manual injection.
- **Doppler/Infisical** – SaaS secret management if limited local infra.
- **Encrypted `.env` (sops + age/gpg)** – lightweight for small teams.

Decide on one mechanism and document access procedures before moving on to Phase 0 Step 3.
