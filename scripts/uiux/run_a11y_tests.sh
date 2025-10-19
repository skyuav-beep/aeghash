#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STORYBOOK_DIR="$ROOT_DIR/examples/frontend-storybook"
LOG_DIR="$ROOT_DIR/docs/uiux/logs"
SERVER_LOG="${TMPDIR:-/tmp}/storybook-a11y.log"
SERVER_PID=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]]; then
    echo "Stopping Storybook static server (pid: ${SERVER_PID})"
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

cd "${STORYBOOK_DIR}"

# Ensure design tokens and dependencies are in sync before building Storybook.
pnpm install --frozen-lockfile
pnpm run tokens:sync

export STORYBOOK_COVERAGE=1
pnpm run storybook:build

# Serve the static build for the test-runner.
pnpm exec http-server storybook-static -p 6006 >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

# Wait until the server responds or fail after timeout.
ATTEMPTS=0
until curl -sSf "http://127.0.0.1:6006/index.html" >/dev/null; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [[ "${ATTEMPTS}" -ge 30 ]]; then
    echo "Storybook static server did not start within 30 seconds. Logs:" >&2
    cat "${SERVER_LOG}" >&2 || true
    exit 1
  fi
  sleep 1
done

# Run the Storybook test-runner with coverage collection enabled.
pnpm exec test-storybook \
  --index-json \
  --coverage \
  --failOnConsole \
  --ci \
  --disable-telemetry \
  --url http://127.0.0.1:6006

# Persist coverage artifact for QA traceability.
mkdir -p "${LOG_DIR}"
COVERAGE_SRC=""
if [[ -f ".nyc_output/coverage.json" ]]; then
  COVERAGE_SRC=".nyc_output/coverage.json"
elif [[ -f "coverage/storybook/coverage-storybook.json" ]]; then
  COVERAGE_SRC="coverage/storybook/coverage-storybook.json"
fi

if [[ -n "${COVERAGE_SRC}" ]]; then
  TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
  DEST="${LOG_DIR}/storybook-a11y-${TIMESTAMP}.json"
  cp "${COVERAGE_SRC}" "${DEST}"
  echo "Saved coverage report to ${DEST}"
else
  echo "Warning: coverage file not found. Skipped log archival." >&2
fi
