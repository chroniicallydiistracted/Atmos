# Local Automation Scripts

Place reproducible automation scripts here:
- `bootstrap.sh` – install prerequisites, create directories, fetch fonts/data (TODO).
- `backup.sh` – snapshot Postgres + MinIO.
- `seed_minio.py` – populate the derived bucket with sample timeline entries for UI testing.
- `seed_postgres.py` – ensure placeholder tables/rows exist in Postgres for local experiments.
- `test.sh` – run API + frontend unit tests (expects dependencies installed via pip/npm).
- `dev-stack.sh` – convenience wrapper around docker compose for bringing the API, ingestion, and frontend services up/down.

Ensure every script is idempotent and documented at the top with usage examples.
