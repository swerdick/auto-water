# AGENTS.md

## Architecture

Refer to `../project-hub/auto-water/` for architectural documents.

## Testing

- Always run `just test` after changing files in the `src/poc/` directory.
- Write new unit tests for any testable code you add to the project. Write tests that cover edge cases and error handling.

## CI

- Always run `just ci` before pushing a commit.

## Containers

- Use `Containerfile` (not Dockerfile) — OCI standard naming.
- Use `podman` commands locally. CI overrides with `CONTAINER_CLI=docker`.
- Base images use Debian bookworm (build) and bookworm-slim (runtime), not Alpine.
- Target platform is `linux/arm64` (Raspberry Pi 5).

## Design Principles

- **Local-first**: data lives on the Pi; sync to laptop is a convenience, not a dependency. The system must work fully offline.
- **Simple over clever**: this is one Pi watering plants, not a distributed system. Avoid over-engineering.
- **Safety by default**: pump OFF is the safe state. Hard limits on pump duration, cooldown between activations.
- **Cost-conscious**: no paid cloud services.
- **Observable**: log everything — sensor readings, pump events, errors.
