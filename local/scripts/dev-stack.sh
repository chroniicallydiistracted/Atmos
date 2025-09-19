#!/usr/bin/env bash
set -euo pipefail

# Helper for managing the local Atmos stack (API + ingestion + frontend).
# Usage:
#   ./local/scripts/dev-stack.sh up       # build and start containers in background
#   ./local/scripts/dev-stack.sh down     # stop containers and remove volumes (optional --keep-data)
#   ./local/scripts/dev-stack.sh logs     # tail logs for core services
#   ./local/scripts/dev-stack.sh seed     # seed MinIO & Postgres with sample data

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
COMPOSE="docker compose -f $COMPOSE_FILE"
PROFILES=(core ingestion frontend)

PROFILE_FLAGS=()
for profile in "${PROFILES[@]}"; do
  PROFILE_FLAGS+=("--profile" "$profile")
done

ensure_env() {
  if [ ! -f "$ROOT_DIR/config/.env" ]; then
    cp "$ROOT_DIR/config/.env.example" "$ROOT_DIR/config/.env"
    echo "[dev-stack] Copied config/.env.example -> config/.env"
  fi
}

python_bin() {
  if [ -x "$ROOT_DIR/../.venv/bin/python" ]; then
    echo "$ROOT_DIR/../.venv/bin/python"
  else
    command -v python3 >/dev/null 2>&1 && echo "python3" || echo "python"
  fi
}

seed_minio() {
  local py
  py=$(python_bin)
  "$py" "$ROOT_DIR/scripts/seed_minio.py"
}

seed_postgres() {
  local py
  py=$(python_bin)
  "$py" "$ROOT_DIR/scripts/seed_postgres.py"
}

cmd_up() {
  ensure_env
  $COMPOSE "${PROFILE_FLAGS[@]}" up -d --build
  echo "[dev-stack] Stack running. Access frontend at http://localhost:4173"
}

cmd_down() {
  local keep_data=0
  if [ "${1:-}" = "--keep-data" ]; then
    keep_data=1
  fi
  if [ "$keep_data" -eq 1 ]; then
    $COMPOSE "${PROFILE_FLAGS[@]}" down
  else
    $COMPOSE "${PROFILE_FLAGS[@]}" down -v
  fi
}

cmd_logs() {
  $COMPOSE "${PROFILE_FLAGS[@]}" logs -f "$@"
}

cmd_seed() {
  ensure_env
  seed_minio
  seed_postgres
  echo "[dev-stack] Seeded MinIO timeline entries and Postgres placeholder data."
}

case "${1:-}" in
  up)
    shift
    cmd_up "$@"
    ;;
  down)
    shift
    cmd_down "$@"
    ;;
  logs)
    shift
    cmd_logs "$@"
    ;;
  seed)
    shift
    cmd_seed "$@"
    ;;
  *)
    cat <<USAGE
Usage: $0 <command>

Commands:
  up             Build/start API, ingestion, and frontend services (detached)
  down [--keep-data]  Stop services; remove volumes unless --keep-data supplied
  logs [services] Tail container logs (defaults to all core services)
  seed           Populate MinIO/Postgres with sample data for UI testing
USAGE
    exit 1
    ;;
esac
