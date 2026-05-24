project_name := "auto-water"
image_tag := env("IMAGE_TAG", "latest")
container_cli := env("CONTAINER_CLI", "podman")

# List all available recipes
default:
    @just --list

# Run the poller locally (stdout sink, no hardware) — Ctrl-C to stop
dev:
    PYTHONPATH=src SINK=stdout python -m auto_water

# Apply pending database migrations (needs DATABASE_URL in env)
migrate:
    PYTHONPATH=src python -m auto_water.migrate up

# Roll back migrations (default to version 0; pass --to N to stop earlier)
migrate-down *args:
    PYTHONPATH=src python -m auto_water.migrate down {{args}}

# Compile/bundle source code (syntax check for Python)
build:
    python -m compileall src

# Run unit tests
test:
    python -m pytest

# Run integration tests
test-integration:
    @echo "No integration tests configured yet"

# Run all static analysis (linters, security scanning)
check:
    ruff check src tests
    bandit -r src
    pip-audit -r requirements.txt

# Format code
fmt:
    ruff format src tests
    ruff check --fix src tests

# Remove build artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

# Build the container image
container-build:
    {{container_cli}} build -t {{project_name}}:{{image_tag}} -f Containerfile .

# Start the project in containers
up:
    {{container_cli}} compose up

# Stop containers
down:
    {{container_cli}} compose down

# Local CI pipeline (lint, test, build — no container)
ci: check test test-integration build

# Full CI pipeline including the container build
ci-full: ci container-build

# Run everything (format + full CI pipeline)
all: fmt ci-full

# Export Grafana dashboards tagged 'auto-water' to grafana-dashboards/.
# Strips Grafana-assigned id/version so re-saves don't churn the diff.
# (Mirrors homelab's backup-grafana; Bitwarden vault must be unlocked.)
backup-grafana:
    #!/usr/bin/env bash
    set -euo pipefail
    GRAFANA_URL="${GRAFANA_URL:-https://grafana.vingilot.internal}"
    GRAFANA_USER="${GRAFANA_USER:-admin}"
    GRAFANA_PASSWORD=$(bw get password grafana-admin)
    OUTDIR="grafana-dashboards"
    mkdir -p "$OUTDIR"
    UIDS=$(curl -fsS -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
        "$GRAFANA_URL/api/search?type=dash-db&tag=auto-water" | jq -r '.[].uid')
    if [[ -z "$UIDS" ]]; then
        echo "No dashboards tagged 'auto-water' found."
        exit 0
    fi
    count=0
    for uid in $UIDS; do
        curl -fsS -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
            "$GRAFANA_URL/api/dashboards/uid/$uid" | \
            jq '.dashboard | del(.id, .version)' > "$OUTDIR/${uid}.json"
        echo "  ✓ ${uid}.json"
        count=$((count + 1))
    done
    echo
    echo "Exported $count dashboard(s) to $OUTDIR/"
