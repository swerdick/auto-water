from __future__ import annotations

import logging

from ..config import Config
from .base import Sensor

logger = logging.getLogger(__name__)


def build_sensors(config: Config) -> list[Sensor]:
    """Construct the enabled sensors from config.

    This is the *only* module that touches the real hardware libraries, and it
    does so lazily so that importing the rest of the package — and running the
    test suite — never needs a Raspberry Pi.
    """
    sensors: list[Sensor] = []

    i2c = _make_i2c() if (config.bh1750.enabled or config.hdc302x.enabled) else None

    if config.bh1750.enabled:
        import adafruit_bh1750

        from .bh1750 import BH1750Sensor

        device = adafruit_bh1750.BH1750(i2c, address=config.bh1750.address)
        sensors.append(BH1750Sensor(device, config.bh1750.sensor_id))
        logger.info("enabled BH1750 at 0x%02x", config.bh1750.address)

    if config.hdc302x.enabled:
        import adafruit_hdc302x

        from .hdc302x import HDC302xSensor

        device = adafruit_hdc302x.HDC302x(i2c, address=config.hdc302x.address)
        sensors.append(HDC302xSensor(device, config.hdc302x.sensor_id))
        logger.info("enabled HDC302x at 0x%02x", config.hdc302x.address)

    if config.ds18b20.enabled:
        from w1thermsensor import W1ThermSensor

        from .ds18b20 import DS18B20Sensor

        for device in W1ThermSensor.get_available_sensors():
            sensors.append(DS18B20Sensor(device))
        logger.info("enabled %d DS18B20 probe(s)", sum(1 for s in sensors if "ds18b20" in s.sensor_id))

    if config.resistive.enabled:
        from gpiozero import DigitalInputDevice

        from .resistive import ResistiveMoistureSensor

        device = DigitalInputDevice(config.resistive.gpio_pin)
        sensors.append(
            ResistiveMoistureSensor(device, config.resistive.sensor_id, config.resistive.dry_when_high)
        )
        logger.info("enabled resistive soil probe on GPIO%d", config.resistive.gpio_pin)

    return sensors


def _make_i2c() -> object:
    import board
    import busio

    return busio.I2C(board.SCL, board.SDA)
