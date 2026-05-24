"""auto-water: sensor-reading service for the Raspberry Pi 5 plant-watering build.

This package replaces the original Flask/Redis deployment test. It polls the
digital sensors wired to the Pi (I²C temp/humidity + light, 1-Wire soil temp,
and a resistive soil probe's wet/dry digital line), and writes readings to a
configurable sink (stdout for the bench, Postgres in production).

No actuation yet — this is the read-only POC for characterizing sensor data
before any watering logic exists.
"""

__version__ = "0.1.0"
