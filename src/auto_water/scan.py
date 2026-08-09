"""Bring-up / calibration helper: ``python -m auto_water.scan``.

Scans the I²C bus (which of 0x48-0x4B respond) and then streams the live raw
ADC count for every configured ADS1115 probe, so you can confirm each board and
channel, capture per-probe dry (in-air) and wet (in-water) calibration values,
and spot dud sensors (a count that barely moves between air and water).

Like ``factory``, this touches the real hardware libraries, so its imports are
lazy — importing the package on a laptop never needs a Raspberry Pi.
"""

from __future__ import annotations

import sys
import time


def _scan_i2c() -> list[int]:
    """Return the I²C addresses that ACK on the bus (via Blinka's busio scan)."""
    import board
    import busio

    i2c = busio.I2C(board.SCL, board.SDA)
    while not i2c.try_lock():
        time.sleep(0.01)  # don't peg a core if the poller holds the bus lock
    try:
        return sorted(i2c.scan())
    finally:
        i2c.unlock()


def _main(argv: list[str] | None = None) -> int:
    import argparse

    from .config import Config

    parser = argparse.ArgumentParser(
        prog="auto_water.scan",
        description="Scan the I²C bus and stream raw ADS1115 counts for bring-up/calibration.",
    )
    parser.add_argument(
        "--interval", type=float, default=1.0, help="seconds between samples (default 1.0)"
    )
    args = parser.parse_args(argv)

    config = Config.from_env()

    present = _scan_i2c()
    print("I²C devices present: " + (", ".join(f"0x{a:02x}" for a in present) or "(none)"))
    for addr in (0x48, 0x49, 0x4A, 0x4B):
        print(f"  ADS1115 @ 0x{addr:02x}: {'FOUND' if addr in present else 'absent'}")

    if not config.ads1115.enabled or not config.ads1115.probes:
        print(
            "\nNo ADS1115 probes configured (set ADS1115_ENABLED=1 and ADS1115_PROBES). "
            "The I²C scan above is still useful for confirming addresses."
        )
        return 0

    import adafruit_ads1x15.ads1115 as ADS
    import board
    import busio
    from adafruit_ads1x15.analog_in import AnalogIn

    i2c = busio.I2C(board.SCL, board.SDA)
    channel_pins = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
    devices: dict[int, object] = {}
    channels: list[tuple[str, object]] = []
    for probe in config.ads1115.probes:
        if probe.address not in devices:
            ads = ADS.ADS1115(i2c, address=probe.address)
            ads.gain = 1
            devices[probe.address] = ads
        label = f"{probe.sensor_id}(0x{probe.address:02x}c{probe.channel})"
        channels.append((label, AnalogIn(devices[probe.address], channel_pins[probe.channel])))

    print("\nLive raw counts (gain=1, ~26400 ≈ 3.3 V). Ctrl-C to stop.")
    print("Dip a probe in AIR -> note the DRY value; in WATER -> note the WET value.")
    print("A probe whose count barely moves between air and water is a DUD.\n")
    print("  " + " | ".join(label for label, _ in channels))
    try:
        while True:
            print("  " + " | ".join(f"{int(ch.value):>6d}" for _, ch in channels), flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
