from __future__ import annotations

from ..models import Reading
from .base import SensorError


class BH1750Sensor:
    """Ambient light (lux) over I²C. Wraps an ``adafruit_bh1750.BH1750`` device."""

    def __init__(self, device: object, sensor_id: str = "bh1750") -> None:
        self.sensor_id = sensor_id
        self._device = device

    def read(self) -> list[Reading]:
        try:
            lux = float(self._device.lux)
        except Exception as exc:  # noqa: BLE001 - normalize any backend failure
            raise SensorError(f"{self.sensor_id}: failed to read lux") from exc
        return [Reading(self.sensor_id, "illuminance", lux, "lux")]
