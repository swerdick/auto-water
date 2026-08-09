from __future__ import annotations

from ..models import Reading
from .base import SensorError


def _to_percent(raw: int, dry_raw: int, wet_raw: int) -> float:
    """Map a raw ADC count to 0-100 % wetness.

    Capacitive v1.2 probes read a *higher* count in air (dry) and a *lower*
    count in water (wet), so ``dry_raw > wet_raw``. Linear between the two
    references, clamped to [0, 100].
    """
    span = dry_raw - wet_raw
    pct = (dry_raw - raw) / span * 100.0
    return max(0.0, min(100.0, pct))


class ADS1115Channel:
    """One capacitive soil-moisture probe on a single ADS1115 channel.

    Wraps an injected ``adafruit_ads1x15.analog_in.AnalogIn`` whose ``.value``
    is the raw signed 16-bit-scaled count. Always emits a ``soil_moisture_raw``
    reading; additionally emits a calibrated ``soil_moisture`` percentage when
    both ``dry_raw`` and ``wet_raw`` are set and differ. Logging raw
    unconditionally means an uncalibrated — or dud — probe still produces a
    signal, and percentages can be re-derived later from stored raw counts if
    the calibration is retuned.
    """

    def __init__(
        self,
        channel: object,
        sensor_id: str,
        dry_raw: int | None = None,
        wet_raw: int | None = None,
    ) -> None:
        self.sensor_id = sensor_id
        self._channel = channel
        self._dry_raw = dry_raw
        self._wet_raw = wet_raw

    def read(self) -> list[Reading]:
        try:
            raw = int(self._channel.value)
        except Exception as exc:  # noqa: BLE001 - normalize any backend failure
            raise SensorError(f"{self.sensor_id}: failed to read ADC channel") from exc
        readings = [Reading(self.sensor_id, "soil_moisture_raw", float(raw), "adc")]
        dry, wet = self._dry_raw, self._wet_raw
        if dry is not None and wet is not None and dry != wet:
            pct = _to_percent(raw, dry, wet)
            readings.append(Reading(self.sensor_id, "soil_moisture", pct, "percent"))
        return readings
