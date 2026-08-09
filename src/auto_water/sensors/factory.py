from __future__ import annotations

import logging

from ..config import ADS1115ProbeConfig, Config
from .base import Sensor

logger = logging.getLogger(__name__)


def build_sensors(config: Config) -> list[Sensor]:
    """Construct the enabled sensors from config.

    This is the *only* module that touches the real hardware libraries, and it
    does so lazily so that importing the rest of the package — and running the
    test suite — never needs a Raspberry Pi.

    Construction is fault-tolerant: a missing or dead device is logged and
    skipped rather than crashing startup, so one absent sensor (or a dud
    capacitive probe) can't take down the whole poller. The Poller already
    isolates per-cycle *read* failures; this extends that same resilience to
    device *construction*. Bus-level failure is equally non-fatal: if the I²C
    bus itself can't be opened, every I²C sensor is skipped in one step and
    non-I²C sensors (DS18B20 on 1-Wire) still run — worst case the poller
    idles on heartbeat alone rather than crash-looping.
    """
    sensors: list[Sensor] = []

    needs_i2c = config.bh1750.enabled or config.hdc302x.enabled or config.ads1115.enabled
    i2c = None
    if needs_i2c:
        try:
            i2c = _make_i2c()
        except Exception:  # noqa: BLE001 - dead/absent bus: degrade, don't crash
            logger.exception(
                "I2C bus unavailable — skipping ALL I2C sensors (BH1750, HDC302x, "
                "ADS1115); non-I2C sensors still run"
            )

    if config.bh1750.enabled and i2c is not None:
        try:
            import adafruit_bh1750

            from .bh1750 import BH1750Sensor

            device = adafruit_bh1750.BH1750(i2c, address=config.bh1750.address)
            sensors.append(BH1750Sensor(device, config.bh1750.sensor_id))
            logger.info("enabled BH1750 at 0x%02x", config.bh1750.address)
        except Exception:  # noqa: BLE001 - skip a dead/absent device, don't crash startup
            logger.exception("failed to init BH1750 at 0x%02x; skipping", config.bh1750.address)

    if config.hdc302x.enabled and i2c is not None:
        try:
            import adafruit_hdc302x

            from .hdc302x import HDC302xSensor

            device = adafruit_hdc302x.HDC302x(i2c, address=config.hdc302x.address)
            sensors.append(HDC302xSensor(device, config.hdc302x.sensor_id))
            logger.info("enabled HDC302x at 0x%02x", config.hdc302x.address)
        except Exception:  # noqa: BLE001
            logger.exception("failed to init HDC302x at 0x%02x; skipping", config.hdc302x.address)

    if config.ds18b20.enabled:
        try:
            from w1thermsensor import W1ThermSensor

            from .ds18b20 import DS18B20Sensor

            probes = W1ThermSensor.get_available_sensors()
            for device in probes:
                serial = str(getattr(device, "id", ""))
                name = config.ds18b20.names.get(serial)
                sensor = DS18B20Sensor(device, f"ds18b20_{name}" if name else None)
                sensors.append(sensor)
                # Log serial -> sensor_id so operators can build DS18B20_NAMES
                # from `kubectl logs` while warming probes one at a time.
                logger.info("enabled DS18B20 %s as %s", serial, sensor.sensor_id)
        except Exception:  # noqa: BLE001
            logger.exception("failed to enumerate DS18B20 probes; skipping")

    if config.ads1115.enabled and i2c is not None:
        _build_ads1115(config, i2c, sensors)

    if config.resistive.enabled:
        try:
            from gpiozero import DigitalInputDevice
        except ImportError as exc:
            raise RuntimeError(
                "RESISTIVE_ENABLED is set but gpiozero is not installed. gpiozero "
                "(plus its lgpio backend and the liblgpio system library) is deferred "
                "from the image until the resistive-sensor / actuation phase — add it "
                "to requirements-hw.txt + the Containerfile to enable this sensor."
            ) from exc

        from .resistive import ResistiveMoistureSensor

        try:
            device = DigitalInputDevice(config.resistive.gpio_pin)
            sensors.append(
                ResistiveMoistureSensor(
                    device, config.resistive.sensor_id, config.resistive.dry_when_high
                )
            )
            logger.info("enabled resistive soil probe on GPIO%d", config.resistive.gpio_pin)
        except Exception:  # noqa: BLE001
            logger.exception(
                "failed to init resistive probe on GPIO%d; skipping", config.resistive.gpio_pin
            )

    return sensors


def _build_ads1115(config: Config, i2c: object, sensors: list[Sensor]) -> None:
    """Add capacitive soil-moisture probes read via one or more ADS1115 ADCs.

    Probes are grouped by I²C address so each physical ADS1115 board is
    constructed once and shared across its (up to four) channels. A dead board
    (a whole address) or a single dud channel is logged and skipped without
    taking down the others.
    """
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    from .ads1115 import ADS1115Channel

    channel_pins = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}

    by_address: dict[int, list[ADS1115ProbeConfig]] = {}
    for probe in config.ads1115.probes:
        by_address.setdefault(probe.address, []).append(probe)

    for address, probes in sorted(by_address.items()):
        try:
            ads = ADS.ADS1115(i2c, address=address)
            ads.gain = 1  # ±4.096 V FS — fits 3.3 V-powered capacitive AOUT without clipping
        except Exception:  # noqa: BLE001 - whole board missing/dead
            logger.exception(
                "failed to init ADS1115 at 0x%02x; skipping %d probe(s)", address, len(probes)
            )
            continue
        for probe in probes:
            try:
                channel = AnalogIn(ads, channel_pins[probe.channel])
                sensors.append(
                    ADS1115Channel(channel, probe.sensor_id, probe.dry_raw, probe.wet_raw)
                )
                calibrated = probe.dry_raw is not None and probe.wet_raw is not None
                logger.info(
                    "enabled ADS1115 probe %s at 0x%02x ch%d (calibrated=%s)",
                    probe.sensor_id,
                    address,
                    probe.channel,
                    calibrated,
                )
            except Exception:  # noqa: BLE001 - single dud channel
                logger.exception(
                    "failed to init ADS1115 probe %s at 0x%02x ch%d; skipping",
                    probe.sensor_id,
                    address,
                    probe.channel,
                )


def _make_i2c() -> object:
    import board
    import busio

    return busio.I2C(board.SCL, board.SDA)
