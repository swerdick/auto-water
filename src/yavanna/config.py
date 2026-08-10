from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

# Heartbeat lives on the container's ephemeral filesystem; the k8s liveness
# probe reads it. /tmp is intentional here, not a tempfile-security concern.
_DEFAULT_HEARTBEAT_PATH = "/tmp/yavanna-healthy"  # noqa: S108  # nosec B108


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
    """DS18B20 waterproof soil-temperature probes over 1-Wire (auto-discovered).

    ``names`` optionally maps a probe's 1-Wire serial (e.g. "3ce1d4438abc" —
    the factory logs each discovered serial at startup) to a plant name.
    Mapped probes get sensor_id ``ds18b20_<name>``; the ``ds18b20_`` prefix is
    composed by the factory so the dashboard's ``LIKE 'ds18b20%'`` query keeps
    matching by construction. Unmapped probes keep their serial-based default.
    """

    enabled: bool = False
    names: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> DS18B20Config:
        return cls(
            enabled=_bool("DS18B20_ENABLED", False),
            names=_parse_ds18b20_names(_str("DS18B20_NAMES", "")),
        )


def _parse_ds18b20_names(raw: str | None) -> dict[str, str]:
    """Parse DS18B20_NAMES — a JSON object of {"<serial>": "<plant name>"}.

    Empty/unset yields no mapping; malformed JSON, a non-object, or an empty
    name raises (fail loud on a config typo rather than silently mislabeling
    a probe — same philosophy as ADS1115_PROBES).
    """
    raw = (raw or "").strip()
    if not raw:
        return {}
    items = json.loads(raw)
    if not isinstance(items, dict):
        raise ValueError("DS18B20_NAMES must be a JSON object of serial -> name")
    names: dict[str, str] = {}
    for serial, name in items.items():
        if not str(name).strip():
            raise ValueError(f"DS18B20_NAMES[{serial!r}]: name must be non-empty")
        names[str(serial)] = str(name).strip()
    return names


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
class ADS1115ProbeConfig:
    """One capacitive soil probe: a channel on an ADS1115 at a given I²C address.

    dry_raw/wet_raw are calibration counts captured with ``python -m
    yavanna.scan`` (dry = in air, wet = in water). When both are set and
    differ, the probe also emits a 0-100 % ``soil_moisture`` reading; otherwise
    only the raw ``soil_moisture_raw`` count is logged.
    """

    address: int  # 0x48 / 0x49 / 0x4A / 0x4B
    channel: int  # 0-3 (A0-A3)
    sensor_id: str
    dry_raw: int | None = None
    wet_raw: int | None = None


@dataclass(frozen=True)
class ADS1115Config:
    """N capacitive soil probes across one or more ADS1115 ADCs on the I²C bus."""

    enabled: bool = False
    probes: tuple[ADS1115ProbeConfig, ...] = ()

    @classmethod
    def from_env(cls) -> ADS1115Config:
        return cls(
            enabled=_bool("ADS1115_ENABLED", False),
            probes=_parse_probes(_str("ADS1115_PROBES", "")),
        )


def _parse_probes(raw: str | None) -> tuple[ADS1115ProbeConfig, ...]:
    """Parse ADS1115_PROBES — a JSON array of probe objects — into a tuple.

    Each entry: ``{"address": "0x48"|72, "channel": 0-3, "sensor_id": "...",
    "dry_raw": int?, "wet_raw": int?}``. Empty/unset yields no probes; malformed
    JSON or a bad entry raises (fail loud on a config typo rather than silently
    dropping a probe).
    """
    raw = (raw or "").strip()
    if not raw:
        return ()
    items = json.loads(raw)
    if not isinstance(items, list):
        raise ValueError("ADS1115_PROBES must be a JSON array")
    probes: list[ADS1115ProbeConfig] = []
    for i, item in enumerate(items):
        addr = item["address"]
        address = int(addr, 0) if isinstance(addr, str) else int(addr)
        channel = int(item["channel"])
        if channel not in (0, 1, 2, 3):
            raise ValueError(f"ADS1115_PROBES[{i}]: channel must be 0-3, got {channel}")
        dry = item.get("dry_raw")
        wet = item.get("wet_raw")
        probes.append(
            ADS1115ProbeConfig(
                address=address,
                channel=channel,
                sensor_id=str(item["sensor_id"]),
                dry_raw=int(dry) if dry is not None else None,
                wet_raw=int(wet) if wet is not None else None,
            )
        )
    return tuple(probes)


@dataclass(frozen=True)
class Config:
    poll_interval_seconds: float = 60.0
    log_level: str = "INFO"
    sink: str = "stdout"  # "stdout" | "postgres"
    database_url: str | None = None
    heartbeat_path: str = _DEFAULT_HEARTBEAT_PATH
    # Retry buffer: readings held in memory while the sink is unreachable (e.g.
    # gondor's nightly downtime or an extended trip). Bounded primarily by a time
    # window (buffer_retention_days); buffer_max is a hard count cap / memory
    # backstop. Both drop oldest first. When buffer_spill_path is set the buffer
    # is mirrored to a SQLite file on sink failure so a pod restart mid-outage
    # doesn't drop it; unset keeps the old in-memory-only behavior.
    buffer_retention_days: float = 30.0
    buffer_max: int = 500_000
    buffer_spill_path: str | None = None
    hdc302x: HDC302xConfig = field(default_factory=HDC302xConfig)
    bh1750: BH1750Config = field(default_factory=BH1750Config)
    ds18b20: DS18B20Config = field(default_factory=DS18B20Config)
    resistive: ResistiveConfig = field(default_factory=ResistiveConfig)
    ads1115: ADS1115Config = field(default_factory=ADS1115Config)

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            poll_interval_seconds=_float("POLL_INTERVAL_SECONDS", 60.0),
            log_level=_str("LOG_LEVEL", "INFO"),
            sink=_str("SINK", "stdout"),
            database_url=_str("DATABASE_URL", None),
            heartbeat_path=_str("HEARTBEAT_PATH", _DEFAULT_HEARTBEAT_PATH),
            buffer_retention_days=_float("BUFFER_RETENTION_DAYS", 30.0),
            buffer_max=_int("BUFFER_MAX", 500_000),
            buffer_spill_path=_str("BUFFER_SPILL_PATH", None),
            hdc302x=HDC302xConfig.from_env(),
            bh1750=BH1750Config.from_env(),
            ds18b20=DS18B20Config.from_env(),
            resistive=ResistiveConfig.from_env(),
            ads1115=ADS1115Config.from_env(),
        )
