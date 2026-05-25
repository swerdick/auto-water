from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from .health import Heartbeat
from .models import Reading
from .sensors.base import Sensor
from .sinks.base import ReadingSink

logger = logging.getLogger(__name__)


class Poller:
    """Polls all sensors on an interval and writes readings to the sink.

    Resilience properties:
      * one failing sensor never stops the others (errors are logged, skipped);
      * a failing sink never loses data immediately — readings accumulate in an
        in-memory retry buffer and flush on the next successful write. The buffer
        is bounded primarily by a **time window** (``retention_seconds``, e.g. 30
        days) so it rides out an extended sink outage (gondor off during a trip),
        with a hard count cap (``buffer_max``) as a memory backstop.
      * a wedged loop is caught by the heartbeat → liveness probe → pod restart.

    NB: the buffer is **in-memory only** — it's lost on a pod restart. It reliably
    covers nightly/multi-day outages; a durable on-disk store (SQLite on a PVC) is
    the proper multi-week solution and is tracked on the homelab ROADMAP.
    """

    def __init__(
        self,
        sensors: list[Sensor],
        sink: ReadingSink,
        *,
        interval: float,
        heartbeat: Heartbeat,
        buffer_max: int = 500_000,
        retention_seconds: float | None = None,
    ) -> None:
        self._sensors = list(sensors)
        self._sink = sink
        self._interval = interval
        self._heartbeat = heartbeat
        self._buffer: deque[Reading] = deque(maxlen=buffer_max)
        self._retention = timedelta(seconds=retention_seconds) if retention_seconds else None
        self._stop = threading.Event()

    def collect(self) -> list[Reading]:
        # Stamp the whole cycle with one timestamp. Sensors are read
        # sequentially and a 1-Wire bus with several DS18B20 probes can spread
        # those reads over seconds, but collapsing a cycle onto a single time
        # means same-cadence series share an x-axis: Grafana then draws multiple
        # probes as continuous lines instead of isolated dots, and a sensor that
        # drops out shows as an honest gap rather than being papered over. The
        # few seconds of intra-cycle read spread is irrelevant for these metrics.
        cycle_at = datetime.now(UTC)
        readings: list[Reading] = []
        for sensor in self._sensors:
            try:
                readings.extend(sensor.read())
            except Exception:  # noqa: BLE001 - deliberate: one sensor must not stop the others
                # Broad on purpose for an unattended device — a single sensor's
                # failure (including unexpected bugs) must not kill the loop or
                # the watering logic. logger.exception records the full traceback,
                # so genuine bugs stay loud in the logs; they're just not fatal.
                logger.exception("sensor %s read failed", getattr(sensor, "sensor_id", "?"))
        return [replace(r, recorded_at=cycle_at) for r in readings]

    def poll_once(self) -> None:
        new = self.collect()
        maxlen = self._buffer.maxlen
        if maxlen and len(self._buffer) + len(new) > maxlen:
            logger.warning(
                "retry buffer hit its hard cap (%d) — dropping oldest; sink unreachable",
                maxlen,
            )
        self._buffer.extend(new)
        self._evict_expired()
        if self._buffer:
            try:
                self._sink.write(list(self._buffer))
                self._buffer.clear()
            except Exception:  # noqa: BLE001 - keep buffered, retry next cycle
                logger.warning("sink write failed; buffering %d reading(s)", len(self._buffer))
        self._heartbeat.touch()

    def _evict_expired(self) -> None:
        """Drop buffered readings older than the retention window. Only bites when
        the sink has been unreachable longer than the window — normally the buffer
        is flushed (and empty) every cycle, so this is a no-op."""
        if self._retention is None:
            return
        cutoff = datetime.now(UTC) - self._retention
        dropped = 0
        while self._buffer and self._buffer[0].recorded_at < cutoff:
            self._buffer.popleft()
            dropped += 1
        if dropped:
            logger.warning(
                "dropped %d buffered reading(s) older than the %s retention window "
                "(sink unreachable that long)",
                dropped,
                self._retention,
            )

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        if not self._sensors:
            logger.warning("no sensors enabled; poller will idle and heartbeat only")
        logger.info("poller starting: %d sensor(s), interval=%ss", len(self._sensors), self._interval)
        while not self._stop.is_set():
            start = time.monotonic()
            self.poll_once()
            elapsed = time.monotonic() - start
            # Wait returns early if stop() is called, so shutdown is prompt.
            self._stop.wait(timeout=max(0.0, self._interval - elapsed))
        self._sink.close()
        logger.info("poller stopped")
