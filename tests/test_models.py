from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from auto_water.models import Reading


def test_reading_defaults_recorded_at_to_utc_now():
    before = datetime.now(UTC)
    reading = Reading("bh1750", "illuminance", 123.4, "lux")
    after = datetime.now(UTC)

    assert reading.recorded_at.tzinfo is not None
    assert before <= reading.recorded_at <= after


def test_reading_is_immutable():
    reading = Reading("bh1750", "illuminance", 1.0, "lux")
    with pytest.raises(FrozenInstanceError):
        reading.value = 2.0  # type: ignore[misc]


def test_reading_accepts_explicit_timestamp():
    ts = datetime(2026, 5, 23, 12, 0, tzinfo=UTC)
    reading = Reading("hdc302x", "temperature", 21.5, "celsius", recorded_at=ts)
    assert reading.recorded_at == ts
