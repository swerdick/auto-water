from __future__ import annotations

import logging
import threading
import time
from collections import deque

from .health import Heartbeat
from .models import Reading
from .sensors.base import Sensor
from .sinks.base import ReadingSink

logger = logging.getLogger(__name__)


class Poller:
    """Polls all sensors on an interval and writes readings to the sink.

    Resilience properties:
      * one failing sensor never stops the others (errors are logged, skipped);
      * a failing sink never loses data immediately — readings accumulate in a
        bounded in-memory buffer and flush on the next successful write;
      * a wedged loop is caught by the heartbeat → liveness probe → pod restart.
    """

    def __init__(
        self,
        sensors: list[Sensor],
        sink: ReadingSink,
        *,
        interval: float,
        heartbeat: Heartbeat,
        buffer_max: int = 10000,
    ) -> None:
        self._sensors = list(sensors)
        self._sink = sink
        self._interval = interval
        self._heartbeat = heartbeat
        self._buffer: deque[Reading] = deque(maxlen=buffer_max)
        self._stop = threading.Event()

    def collect(self) -> list[Reading]:
        readings: list[Reading] = []
        for sensor in self._sensors:
            try:
                readings.extend(sensor.read())
            except Exception:  # noqa: BLE001 - one bad sensor must not stop the rest
                logger.exception("sensor %s read failed", getattr(sensor, "sensor_id", "?"))
        return readings

    def poll_once(self) -> None:
        self._buffer.extend(self.collect())
        if self._buffer:
            try:
                self._sink.write(list(self._buffer))
                self._buffer.clear()
            except Exception:  # noqa: BLE001 - keep buffered, retry next cycle
                logger.warning("sink write failed; buffering %d reading(s)", len(self._buffer))
        self._heartbeat.touch()

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
