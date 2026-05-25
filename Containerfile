# auto-water sensor poller. Target platform: linux/arm64 (Raspberry Pi 5).
# Build stage
FROM docker.io/library/python:3.13-trixie AS builder

# Build the lg (lgpio) C library from source — there's no Debian package or
# prebuilt wheel, and Blinka's `import board` on the Pi 5 (bcm2712) requires the
# lgpio Python binding, which links against this lib.
RUN apt-get update && apt-get install -y --no-install-recommends swig wget make \
    && wget -qO /tmp/lg.tar.gz https://github.com/joan2937/lg/archive/refs/heads/master.tar.gz \
    && tar xzf /tmp/lg.tar.gz -C /tmp \
    && make -C /tmp/lg-master install \
    && ldconfig \
    && rm -rf /tmp/lg* /var/lib/apt/lists/*

WORKDIR /src
COPY requirements.txt requirements-hw.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt -r requirements-hw.txt

# Runtime stage
FROM docker.io/library/python:3.13-slim-trixie

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
# liblgpio.so is loaded at runtime by the lgpio Python module's C extension.
COPY --from=builder /usr/local/lib/liblgpio.so* /usr/local/lib/
RUN ldconfig
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
