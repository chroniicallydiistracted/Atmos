#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

run_api_tests() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "[test] python3 not found; skipping API tests" >&2
    return 0
  fi
  python3 -m pytest "$ROOT_DIR/services/api/tests" || {
    echo "[test] API tests failed. Did you install dependencies? (pip install -r services/api/requirements.txt)" >&2
    return 1
  }
}

run_frontend_tests() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "[test] npm not found; skipping frontend tests" >&2
    return 0
  fi
  (
    cd "$ROOT_DIR/services/frontend"
    npm test
  ) || {
    echo "[test] Frontend tests failed. Did you run npm install?" >&2
    return 1
  }
}

run_api_tests
run_frontend_tests
