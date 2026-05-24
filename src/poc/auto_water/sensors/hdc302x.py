from __future__ import annotations

from ..models import Reading
from .base import SensorError


class HDC302xSensor:
    """Temperature + relative humidity over I²C.

    Wraps an ``adafruit_hdc302x.HDC302x`` device, which exposes ``.temperature``
    (°C) and ``.relative_humidity`` (%).
    """

    def __init__(self, device: object, sensor_id: str = "hdc302x") -> None:
        self.sensor_id = sensor_id
        self._device = device

    def read(self) -> list[Reading]:
        try:
            temperature = float(self._device.temperature)
            humidity = float(self._device.relative_humidity)
        except Exception as exc:  # noqa: BLE001 - normalize any backend failure
            raise SensorError(f"{self.sensor_id}: failed to read temp/humidity") from exc
        return [
            Reading(self.sensor_id, "temperature", temperature, "celsius"),
            Reading(self.sensor_id, "humidity", humidity, "percent"),
        ]
