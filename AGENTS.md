# AGENTS.md

## Architecture

Refer to `../project-hub/yavanna/` for architectural documents.

## Testing

- Always run `just test` after changing files in the `src/` directory.
- Write new unit tests for any testable code you add to the project. Write tests that cover edge cases and error handling.

## CI

- Always run `just ci` before pushing a commit (or `just ci-full` to also build the container image).

## Commits & Release

Use conventional commits (`type(scope): description` — feat, fix, refactor,
build, ci, docs, test, chore). Releases are managed by release-please
(single repo-wide version, manifest mode).

- Merges to `main` accumulate on an auto-maintained release PR; merging that
  PR tags `vX.Y.Z`, creates a GitHub release, and triggers the only automatic
  production deploy: the arm64 image is built and pushed to GHCR tagged with
  the plain semver + `latest`, and the release commit pins that tag in
  `deploy/kustomization.yaml`, so Flux rolls the deployment on samwise.
- Regular merges to `main` do NOT deploy. Manual redeploy/rebuild: run
  `deploy.yaml` via workflow_dispatch with the `image-tag` input (select the
  matching `vX.Y.Z` tag under "Use workflow from" to rebuild that release).
- Only `feat`/`fix`/breaking commits create or bump the release PR. To force
  a version, add a `Release-As: X.Y.Z` footer to a commit body.
- After a release merge, Flux may briefly race the ~5-minute arm64 build: a
  transient ImagePullBackOff on the pod resolves itself once the push
  completes (the spill buffer preserves unsent readings across the restart).

## Containers

- Use `Containerfile` (not Dockerfile) — OCI standard naming.
- Use `podman` commands locally. CI overrides with `CONTAINER_CLI=docker`.
- Base images use Debian trixie (build) and trixie-slim (runtime), not Alpine.
- Target platform is `linux/arm64` (Raspberry Pi 5).

## Design Principles

- **Local-first**: data lives on the Pi; sync to laptop is a convenience, not a dependency. The system must work fully offline.
- **Simple over clever**: this is one Pi watering plants, not a distributed system. Avoid over-engineering.
- **Safety by default**: pump OFF is the safe state. Hard limits on pump duration, cooldown between activations.
- **Cost-conscious**: no paid cloud services.
- **Observable**: log everything — sensor readings, pump events, errors.
