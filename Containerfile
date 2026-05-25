# auto-water sensor poller. Target platform: linux/arm64 (Raspberry Pi 5).
# Build stage
FROM docker.io/library/python:3.13-trixie AS builder

WORKDIR /src
COPY requirements.txt requirements-hw.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt -r requirements-hw.txt

# Runtime stage
FROM docker.io/library/python:3.13-slim-trixie

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
WORKDIR /app
COPY src/auto_water ./auto_water

RUN useradd -u 1000 appuser
USER appuser

ENV PYTHONUNBUFFERED=1

# GPIO / I²C / 1-Wire device access is granted at runtime by the k8s
# securityContext (device mounts / privileged) — the image itself is plain.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-m", "auto_water.health"]

CMD ["python", "-m", "auto_water"]
