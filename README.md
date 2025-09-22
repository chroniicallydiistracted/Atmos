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
3. Build images (first time or after code/dep changes):
	```bash
	docker compose build --pull --no-cache
	```
4. Start the stack:
	```bash
	docker compose up -d
	```
5. Tail logs (optional):
	```bash
	docker compose logs -f --tail=100 api ingestion frontend tiler
	```
6. Access frontend (Map + Radar loop) at: http://localhost:4173 (default Vite preview port exposed by compose) or whichever port you set in `docker-compose.yml`.

### Rebuild Fast Path

After typical code edits (no new system libs):
```bash
docker compose build api ingestion frontend && docker compose up -d
```

### NEXRAD Radar Loop Operations

Real multi-frame Level II ingestion & animation is implemented. See `docs/radar-loop.md` for deep details. Core actions:

Trigger new frames (example: 4 frames, 60 min lookback, site KTLX):
```bash
curl -X POST http://localhost:8081/v1/trigger/nexrad-frames \
  -H 'Content-Type: application/json' \
  -d '{"parameters":{"site":"KTLX","frames":4,"lookback_minutes":60}}'
```

List current frames:
```bash
curl http://localhost:8081/v1/radar/nexrad/KTLX/frames | jq
```

COGs + index (inside the `derived` bucket) canonical path pattern:
```
nexrad/<SITE>/<TIMESTAMP>/tilt0_reflectivity.tif
nexrad/<SITE>/<TIMESTAMP>/tilt0_reflectivity.json
indices/radar/nexrad/<SITE>/frames.json
```

All legacy prefixes have been fully removed; only the canonical layout above is valid. Previous migration tooling has been deleted.

### Frontend Animation

The frontend polls frames and cycles them (~400 ms). No synthetic fallback exists; absence of data means no animation until ingestion runs.

### Validation (Headless Loop Check)

Run the headless validation script (ensures real frame changes, not static):
```bash
node scripts/validate_nexrad_loop.ts
```

Prereq: Ensure at least one trigger run completed beforehand (script can optionally issue a trigger if coded to do so).

### Environment Variables

See the consolidated reference in `docs/environment.md` for all supported variables and deprecated aliases. Typical adjustments are made in `config/.env`. Restart affected services after edits:
```bash
docker compose up -d ingestion api frontend
```

### Clean Reset

Wipe containers + volumes (irreversible locally):
```bash
docker compose down -v
```

Then rebuild as above.

## Legacy Reference

If you need to look up AWS-specific implementations or previous experiments, refer to the root repository (especially `services/`, `docs/`, and `infra/`). The new stack should avoid copying code blindly—only port components after they are verified and refit for the local architecture.

## Documentation Map

- Local architecture overview: `docs/architecture.md`
- Service responsibilities and contracts: `docs/services.md`
- Radar loop implementation: `docs/radar-loop.md`
- Migration tracking: see root `docs/migration-off-aws.md`
