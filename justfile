project_name := "auto-water"
image_tag := env("IMAGE_TAG", "latest")
container_cli := env("CONTAINER_CLI", "podman")

# List all available recipes
default:
    @just --list

# Start local development environment
dev:
    cd src/poc && flask run --reload

# Compile/bundle source code (syntax check for Python)
build:
    python -m compileall src/poc/

# Run unit tests
test:
    cd src/poc && python -m pytest

# Run integration tests
test-integration:
    @echo "No integration tests configured yet"

# Run all static analysis (linters, security scanning)
check:
    cd src/poc && ruff check .
    cd src/poc && bandit -r . --exclude ./tests
    cd src/poc && pip-audit -r requirements.txt

# Format code
fmt:
    cd src/poc && ruff format .
    cd src/poc && ruff check --fix .

# Remove build artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true

# Build the container image
container-build:
    {{container_cli}} build -t {{project_name}}:{{image_tag}} -f src/poc/Containerfile src/poc/

# Start the project in containers
up:
    cd src/poc && {{container_cli}}-compose up

# Stop containers
down:
    cd src/poc && {{container_cli}}-compose down

# Run the full CI pipeline locally
ci: check test test-integration build container-build

# Run everything (format + CI pipeline)
all: fmt ci
