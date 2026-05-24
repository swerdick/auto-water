from __future__ import annotations

from ..models import Reading
from .base import SensorError


class DS18B20Sensor:
    """Soil temperature over 1-Wire.

    Wraps a ``w1thermsensor.W1ThermSensor`` device (exposes ``.id`` and
    ``.get_temperature()``). The sensor_id defaults to the probe's unique
    1-Wire serial so multiple chained probes stay distinguishable.
    """

    def __init__(self, device: object, sensor_id: str | None = None) -> None:
        self._device = device
        self.sensor_id = sensor_id or f"ds18b20_{getattr(device, 'id', 'unknown')}"

    def read(self) -> list[Reading]:
        try:
            celsius = float(self._device.get_temperature())
        except Exception as exc:  # noqa: BLE001 - normalize any backend failure
            raise SensorError(f"{self.sensor_id}: failed to read temperature") from exc
        return [Reading(self.sensor_id, "temperature", celsius, "celsius")]
