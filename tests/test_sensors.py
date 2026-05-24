import pytest

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
    ],
)
def test_sensor_failure_raises_sensor_error(sensor):
    with pytest.raises(SensorError):
        sensor.read()
