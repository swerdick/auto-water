import logging
import sys
import types

import pytest

from auto_water.config import BH1750Config, Config, DS18B20Config
from auto_water.sensors import factory
from auto_water.sensors.ads1115 import ADS1115Channel, _to_percent
from auto_water.sensors.base import SensorError
from auto_water.sensors.bh1750 import BH1750Sensor
from auto_water.sensors.ds18b20 import DS18B20Sensor
from auto_water.sensors.hdc302x import HDC302xSensor
from auto_water.sensors.resistive import ResistiveMoistureSensor


class FakeLux:
    def __init__(self, lux):
        self.lux = lux


class FakeHDC:
    def __init__(self, temperature, relative_humidity):
        self.temperature = temperature
        self.relative_humidity = relative_humidity


class FakeW1:
    def __init__(self, temp, id="abc123"):
        self._temp = temp
        self.id = id

    def get_temperature(self):
        return self._temp


class FakeDigital:
    def __init__(self, value):
        self.value = value


class FakeAnalogIn:
    def __init__(self, value):
        self.value = value


class Boom:
    """A device that raises on any attribute access used by the sensors."""

    @property
    def lux(self):
        raise OSError("bus error")

    @property
    def temperature(self):
        raise OSError("bus error")

    def get_temperature(self):
        raise OSError("bus error")

    @property
    def value(self):
        raise OSError("bus error")


def test_bh1750_reads_lux():
    readings = BH1750Sensor(FakeLux(321.0)).read()
    assert len(readings) == 1
    assert readings[0].metric == "illuminance"
    assert readings[0].unit == "lux"
    assert readings[0].value == 321.0


def test_hdc302x_reads_temp_and_humidity():
    readings = HDC302xSensor(FakeHDC(21.5, 48.0), sensor_id="env").read()
    metrics = {r.metric: r for r in readings}
    assert metrics["temperature"].value == 21.5
    assert metrics["temperature"].unit == "celsius"
    assert metrics["humidity"].value == 48.0
    assert metrics["humidity"].unit == "percent"
    assert all(r.sensor_id == "env" for r in readings)


def test_ds18b20_reads_temp_and_derives_id():
    sensor = DS18B20Sensor(FakeW1(19.25, id="28-00000a"))
    assert sensor.sensor_id == "ds18b20_28-00000a"
    readings = sensor.read()
    assert readings[0].metric == "temperature"
    assert readings[0].value == 19.25


def test_ads1115_raw_only_when_uncalibrated():
    readings = ADS1115Channel(FakeAnalogIn(18000), sensor_id="soil_a1").read()
    assert len(readings) == 1
    assert readings[0].sensor_id == "soil_a1"
    assert readings[0].metric == "soil_moisture_raw"
    assert readings[0].unit == "adc"
    assert readings[0].value == 18000.0


def test_ads1115_emits_percent_when_calibrated():
    readings = ADS1115Channel(
        FakeAnalogIn(19000), sensor_id="soil_a1", dry_raw=26000, wet_raw=12000
    ).read()
    metrics = {r.metric: r for r in readings}
    assert metrics["soil_moisture_raw"].value == 19000.0
    assert metrics["soil_moisture"].unit == "percent"
    assert metrics["soil_moisture"].value == pytest.approx(50.0)


def test_ads1115_equal_dry_wet_is_uncalibrated():
    readings = ADS1115Channel(
        FakeAnalogIn(15000), sensor_id="x", dry_raw=20000, wet_raw=20000
    ).read()
    assert [r.metric for r in readings] == ["soil_moisture_raw"]


def test_to_percent_maps_and_clamps():
    assert _to_percent(26000, 26000, 12000) == 0.0
    assert _to_percent(12000, 26000, 12000) == 100.0
    assert _to_percent(19000, 26000, 12000) == pytest.approx(50.0)
    assert _to_percent(30000, 26000, 12000) == 0.0  # drier than dry -> clamp 0
    assert _to_percent(9000, 26000, 12000) == 100.0  # wetter than wet -> clamp 100


def test_resistive_polarity_dry_when_high():
    dry = ResistiveMoistureSensor(FakeDigital(1), dry_when_high=True).read()[0]
    wet = ResistiveMoistureSensor(FakeDigital(0), dry_when_high=True).read()[0]
    assert dry.value == 1.0
    assert wet.value == 0.0
    assert dry.metric == "soil_moisture_digital"


def test_resistive_polarity_inverted():
    dry = ResistiveMoistureSensor(FakeDigital(0), dry_when_high=False).read()[0]
    wet = ResistiveMoistureSensor(FakeDigital(1), dry_when_high=False).read()[0]
    assert dry.value == 1.0
    assert wet.value == 0.0


@pytest.mark.parametrize(
    "sensor",
    [
        BH1750Sensor(Boom()),
        HDC302xSensor(Boom()),
        DS18B20Sensor(Boom(), sensor_id="x"),
        ResistiveMoistureSensor(Boom()),
        ADS1115Channel(Boom(), sensor_id="x"),
    ],
)
def test_sensor_failure_raises_sensor_error(sensor):
    with pytest.raises(SensorError):
        sensor.read()


# --- build_sensors (factory) -------------------------------------------------
# CI has no hardware libraries, so the real `import w1thermsensor` inside the
# factory would be caught-and-skipped; a fake module makes the DS18B20 branch
# actually run so its behavior is assertable.


def _fake_w1_module(devices):
    module = types.ModuleType("w1thermsensor")

    class W1ThermSensor:
        @staticmethod
        def get_available_sensors():
            return list(devices)

    module.W1ThermSensor = W1ThermSensor
    return module


def _raise_bus_error():
    raise OSError("no I2C bus")


def test_build_sensors_survives_i2c_bus_failure(monkeypatch, caplog):
    monkeypatch.setattr(factory, "_make_i2c", _raise_bus_error)
    monkeypatch.setitem(sys.modules, "w1thermsensor", _fake_w1_module([FakeW1(20.0, id="aaa")]))
    config = Config(
        bh1750=BH1750Config(enabled=True),
        ds18b20=DS18B20Config(enabled=True),
    )
    with caplog.at_level(logging.ERROR, logger="auto_water.sensors.factory"):
        sensors = factory.build_sensors(config)
    # The dead bus takes out the I2C sensors in one step; 1-Wire still runs.
    assert [s.sensor_id for s in sensors] == ["ds18b20_aaa"]
    assert "I2C bus unavailable" in caplog.text
    assert "failed to init BH1750" not in caplog.text  # skipped, not attempted


def test_build_sensors_i2c_failure_with_only_i2c_sensors_returns_empty(monkeypatch, caplog):
    monkeypatch.setattr(factory, "_make_i2c", _raise_bus_error)
    config = Config(bh1750=BH1750Config(enabled=True))
    with caplog.at_level(logging.ERROR, logger="auto_water.sensors.factory"):
        sensors = factory.build_sensors(config)
    # Empty list → the poller's existing idle-and-heartbeat path, not a crash.
    assert sensors == []
    assert "I2C bus unavailable" in caplog.text


def test_build_sensors_maps_ds18b20_names(monkeypatch):
    devices = [FakeW1(20.0, id="aaa"), FakeW1(21.0, id="bbb")]
    monkeypatch.setitem(sys.modules, "w1thermsensor", _fake_w1_module(devices))
    config = Config(ds18b20=DS18B20Config(enabled=True, names={"aaa": "basil"}))
    sensors = factory.build_sensors(config)
    # Mapped probe reads as the plant (prefix composed by the factory, so the
    # dashboard's LIKE 'ds18b20%' keeps matching); unmapped keeps its serial.
    assert {s.sensor_id for s in sensors} == {"ds18b20_basil", "ds18b20_bbb"}
