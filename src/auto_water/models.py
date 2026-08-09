from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Reading:
    """A single sensor measurement.

    Stored one row per metric ("long" format): a sensor that emits several
    quantities (e.g. the HDC3022 reports both temperature and humidity) turns
    into several Readings. This shape is what Grafana's Postgres time-series
    queries like best — filter on ``recorded_at``, ``GROUP BY metric``.
    """

    sensor_id: str
    metric: str  # "temperature" | "humidity" | "illuminance" | "soil_moisture" | "soil_moisture_raw" | "soil_moisture_digital"  # noqa: E501
    value: float
    unit: str  # "celsius" | "percent" | "lux" | "adc" | "dry_bool"
    recorded_at: datetime = field(default_factory=_utcnow)
