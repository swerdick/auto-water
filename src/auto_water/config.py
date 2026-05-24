from __future__ import annotations

import os
from dataclasses import dataclass, field

# Heartbeat lives on the container's ephemeral filesystem; the k8s liveness
# probe reads it. /tmp is intentional here, not a tempfile-security concern.
_DEFAULT_HEARTBEAT_PATH = "/tmp/auto-water-healthy"  # noqa: S108  # nosec B108


def _str(name: str, default: str | None) -> str | None:
    raw = os.getenv(name)
    return raw if raw not in (None, "") else default


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw not in (None, "") else default


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw not in (None, "") else default


def _addr(name: str, default: int) -> int:
    """Parse an I²C address from env, accepting hex ("0x44") or decimal ("68")."""
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return int(raw, 0)


@dataclass(frozen=True)
class HDC302xConfig:
    """Adafruit HDC3022 temperature + humidity over I²C (default addr 0x44)."""

    enabled: bool = False
    address: int = 0x44
    sensor_id: str = "hdc302x"

    @classmethod
    def from_env(cls) -> HDC302xConfig:
        return cls(
            enabled=_bool("HDC302X_ENABLED", False),
            address=_addr("HDC302X_ADDRESS", 0x44),
            sensor_id=_str("HDC302X_SENSOR_ID", "hdc302x"),
        )


@dataclass(frozen=True)
class BH1750Config:
    """GY-302 / BH1750 ambient light over I²C (default addr 0x23)."""

    enabled: bool = False
    address: int = 0x23
    sensor_id: str = "bh1750"

    @classmethod
    def from_env(cls) -> BH1750Config:
        return cls(
            enabled=_bool("BH1750_ENABLED", False),
            address=_addr("BH1750_ADDRESS", 0x23),
            sensor_id=_str("BH1750_SENSOR_ID", "bh1750"),
        )


@dataclass(frozen=True)
class DS18B20Config:
    """DS18B20 waterproof soil-temperature probes over 1-Wire (auto-discovered)."""

    enabled: bool = False

    @classmethod
    def from_env(cls) -> DS18B20Config:
        return cls(enabled=_bool("DS18B20_ENABLED", False))


@dataclass(frozen=True)
class ResistiveConfig:
    """Resistive soil probe via an LM393 comparator's digital (wet/dry) output."""

    enabled: bool = False
    gpio_pin: int = 17
    # Common LM393 board polarity: DO reads HIGH when drier than the trimpot
    # threshold. Flip this if your board is wired the other way.
    dry_when_high: bool = True
    sensor_id: str = "resistive_soil"

    @classmethod
    def from_env(cls) -> ResistiveConfig:
        return cls(
            enabled=_bool("RESISTIVE_ENABLED", False),
            gpio_pin=_int("RESISTIVE_GPIO_PIN", 17),
            dry_when_high=_bool("RESISTIVE_DRY_WHEN_HIGH", True),
            sensor_id=_str("RESISTIVE_SENSOR_ID", "resistive_soil"),
        )


@dataclass(frozen=True)
class Config:
    poll_interval_seconds: float = 60.0
    log_level: str = "INFO"
    sink: str = "stdout"  # "stdout" | "postgres"
    database_url: str | None = None
    heartbeat_path: str = _DEFAULT_HEARTBEAT_PATH
    # Cap on the retry buffer (readings held in memory while the sink is
    # unreachable, e.g. during gondor's nightly downtime). Oldest drop first.
    buffer_max: int = 10000
    hdc302x: HDC302xConfig = field(default_factory=HDC302xConfig)
    bh1750: BH1750Config = field(default_factory=BH1750Config)
    ds18b20: DS18B20Config = field(default_factory=DS18B20Config)
    resistive: ResistiveConfig = field(default_factory=ResistiveConfig)

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            poll_interval_seconds=_float("POLL_INTERVAL_SECONDS", 60.0),
            log_level=_str("LOG_LEVEL", "INFO"),
            sink=_str("SINK", "stdout"),
            database_url=_str("DATABASE_URL", None),
            heartbeat_path=_str("HEARTBEAT_PATH", _DEFAULT_HEARTBEAT_PATH),
            buffer_max=_int("BUFFER_MAX", 10000),
            hdc302x=HDC302xConfig.from_env(),
            bh1750=BH1750Config.from_env(),
            ds18b20=DS18B20Config.from_env(),
            resistive=ResistiveConfig.from_env(),
        )
