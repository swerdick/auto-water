from __future__ import annotations

from ..models import Reading
from .base import SensorError


class ResistiveMoistureSensor:
    """Resistive soil probe read through an LM393 comparator's digital output.

    The DO line is a thresholded wet/dry signal (the trimpot sets the point),
    so this yields a boolean, not a moisture *level*. We record the interpreted
    dryness as 1.0 (dry) / 0.0 (wet). ``dry_when_high`` matches the common board
    polarity where DO is HIGH when drier than the threshold.

    (Moisture *levels* come later from the capacitive sensors via the ADS1115.)
    """

    def __init__(
        self,
        device: object,
        sensor_id: str = "resistive_soil",
        dry_when_high: bool = True,
    ) -> None:
        self.sensor_id = sensor_id
        self._device = device
        self._dry_when_high = dry_when_high

    def read(self) -> list[Reading]:
        try:
            raw = int(self._device.value)
        except Exception as exc:  # noqa: BLE001 - normalize any backend failure
            raise SensorError(f"{self.sensor_id}: failed to read digital output") from exc
        is_dry = (raw == 1) if self._dry_when_high else (raw == 0)
        return [Reading(self.sensor_id, "soil_moisture_digital", 1.0 if is_dry else 0.0, "dry_bool")]
