from __future__ import annotations

from typing import Protocol

from ..models import Reading


class SensorError(Exception):
    """Raised when a sensor cannot be read."""


class Sensor(Protocol):
    sensor_id: str

    def read(self) -> list[Reading]:
        """Return current readings, or raise :class:`SensorError` on failure."""
        ...
