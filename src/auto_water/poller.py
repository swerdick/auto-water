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
from .spill import SpillStore

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
      * with a ``spill`` store, the buffer is mirrored to disk on each failed
        write and reloaded at startup, so a pod restart mid-outage doesn't drop
        it. Healthy cycles never touch the spill (its file only sees writes
        while the sink is down), and a broken spill degrades to the in-memory
        behavior — never the other way around.
      * a wedged loop is caught by the heartbeat → liveness probe → pod restart.
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
        spill: SpillStore | None = None,
    ) -> None:
        self._sensors = list(sensors)
        self._sink = sink
        self._interval = interval
        self._heartbeat = heartbeat
        self._buffer: deque[Reading] = deque(maxlen=buffer_max)
        self._retention = timedelta(seconds=retention_seconds) if retention_seconds else None
        self._spill = spill
        self._stop = threading.Event()
        if spill is not None:
            # Rows stay in the file until the first successful flush, so a
            # crash between restore and flush still can't lose them.
            restored = spill.load()
            if self._buffer.maxlen and len(restored) > self._buffer.maxlen:
                # Same oldest-first drop the in-memory cap applies — but say so.
                logger.warning(
                    "restored spill (%d) exceeds the buffer cap (%d); dropping the oldest %d",
                    len(restored),
                    self._buffer.maxlen,
                    len(restored) - self._buffer.maxlen,
                )
            self._buffer.extend(restored)
            if restored:
                # Prune the file to the same bounds memory just applied, so
                # disk and deque stay in lockstep from the first cycle — a
                # later clear() can then never discard rows that only ever
                # existed on disk.
                spill.prune(self._retention_cutoff(), self._buffer.maxlen or len(restored))

    def _retention_cutoff(self) -> datetime:
        if self._retention:
            return datetime.now(UTC) - self._retention
        return datetime.min.replace(tzinfo=UTC)

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
                if self._spill is not None:
                    self._spill.clear()
            except Exception:  # noqa: BLE001 - keep buffered, retry next cycle
                logger.warning("sink write failed; buffering %d reading(s)", len(self._buffer))
                if self._spill is not None:
                    # Mirror only this cycle's new readings — earlier buffered
                    # rows are already in the file — then re-apply the memory
                    # bounds so file and deque stay in lockstep.
                    self._spill.append(new)
                    self._spill.prune(self._retention_cutoff(), self._buffer.maxlen or len(self._buffer))
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
        if self._spill is not None:
            self._spill.close()
        logger.info("poller stopped")
