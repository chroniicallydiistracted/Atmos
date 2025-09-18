# AtmosInsight Local Rebuild

This directory is the new source of truth for the local-first implementation of AtmosInsight. Everything here is designed without AWS dependencies. The legacy code in the repository root remains as historical reference only.

## Contents

- `docs/` – Architecture, runbooks, and design notes specific to the rebuilt stack (see `docs/stack-plan.md` for milestone roadmap).
- `services/` – Source code for new ingestion, rendering, API, and supporting services.
- `config/` – Shared configuration templates (e.g., environment variables, TLS, secrets placeholders).
- `scripts/` – Local automation helpers (setup, backup, testing).
- `docker-compose.yml` – Orchestrates the local services.

## Getting Started

1. Copy `config/.env.example` to `config/.env` and customize values.
2. Install prerequisites listed in `docs/prerequisites.md`.
3. Run `docker compose up` from this directory once services are implemented.

## Legacy Reference

If you need to look up AWS-specific implementations or previous experiments, refer to the root repository (especially `services/`, `docs/`, and `infra/`). The new stack should avoid copying code blindly—only port components after they are verified and refit for the local architecture.

## Documentation Map

- Local architecture overview: `docs/architecture.md`
- Service responsibilities and contracts: `docs/services.md`
- Migration tracking: see root `docs/migration-off-aws.md`
