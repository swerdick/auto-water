import pytest

from auto_water.config import Config


def test_defaults_when_env_unset(monkeypatch):
    # Clear every env var Config.from_env reads, so a value present in the
    # runner's environment can't make this defaults test flaky.
    for key in (
        "POLL_INTERVAL_SECONDS",
        "LOG_LEVEL",
        "SINK",
        "DATABASE_URL",
        "HEARTBEAT_PATH",
        "BUFFER_MAX",
        "BUFFER_RETENTION_DAYS",
        "HDC302X_ENABLED",
        "HDC302X_ADDRESS",
        "HDC302X_SENSOR_ID",
        "BH1750_ENABLED",
        "BH1750_ADDRESS",
        "BH1750_SENSOR_ID",
        "DS18B20_ENABLED",
        "DS18B20_NAMES",
        "BUFFER_SPILL_PATH",
        "RESISTIVE_ENABLED",
        "RESISTIVE_GPIO_PIN",
        "RESISTIVE_DRY_WHEN_HIGH",
        "RESISTIVE_SENSOR_ID",
        "ADS1115_ENABLED",
        "ADS1115_PROBES",
    ):
        monkeypatch.delenv(key, raising=False)
    config = Config.from_env()
    assert config.poll_interval_seconds == 60.0
    assert config.sink == "stdout"
    assert config.database_url is None
    assert config.bh1750.enabled is False
    assert config.bh1750.address == 0x23
    assert config.hdc302x.address == 0x44
    assert config.resistive.gpio_pin == 17
    assert config.resistive.dry_when_high is True
    assert config.buffer_retention_days == 30.0
    assert config.buffer_max == 500_000
    assert config.ads1115.enabled is False
    assert config.ads1115.probes == ()
    assert config.ds18b20.names == {}
    assert config.buffer_spill_path is None


def test_from_env_reads_core_values(monkeypatch):
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "10")
    monkeypatch.setenv("SINK", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://x/y")
    monkeypatch.setenv("BUFFER_MAX", "5")
    config = Config.from_env()
    assert config.poll_interval_seconds == 10.0
    assert config.sink == "postgres"
    assert config.database_url == "postgresql://x/y"
    assert config.buffer_max == 5


def test_bool_parsing_variants(monkeypatch):
    for raw in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("BH1750_ENABLED", raw)
        assert Config.from_env().bh1750.enabled is True
    for raw in ("0", "false", "no", "off", ""):
        monkeypatch.setenv("BH1750_ENABLED", raw)
        assert Config.from_env().bh1750.enabled is False


def test_i2c_address_accepts_hex_and_decimal(monkeypatch):
    monkeypatch.setenv("HDC302X_ADDRESS", "0x45")
    assert Config.from_env().hdc302x.address == 0x45
    monkeypatch.setenv("HDC302X_ADDRESS", "69")
    assert Config.from_env().hdc302x.address == 69


def test_resistive_sensor_config(monkeypatch):
    monkeypatch.setenv("RESISTIVE_ENABLED", "1")
    monkeypatch.setenv("RESISTIVE_GPIO_PIN", "27")
    monkeypatch.setenv("RESISTIVE_DRY_WHEN_HIGH", "false")
    monkeypatch.setenv("RESISTIVE_SENSOR_ID", "pot-a")
    cfg = Config.from_env().resistive
    assert cfg.enabled is True
    assert cfg.gpio_pin == 27
    assert cfg.dry_when_high is False
    assert cfg.sensor_id == "pot-a"


def test_ads1115_probes_parse(monkeypatch):
    monkeypatch.setenv("ADS1115_ENABLED", "1")
    monkeypatch.setenv(
        "ADS1115_PROBES",
        '[{"address":"0x48","channel":0,"sensor_id":"soil_a1","dry_raw":26000,"wet_raw":12000},'
        '{"address":73,"channel":2,"sensor_id":"soil_b1"}]',
    )
    cfg = Config.from_env().ads1115
    assert cfg.enabled is True
    assert len(cfg.probes) == 2
    a1, b1 = cfg.probes
    assert a1.address == 0x48
    assert a1.channel == 0
    assert a1.sensor_id == "soil_a1"
    assert a1.dry_raw == 26000
    assert a1.wet_raw == 12000
    assert b1.address == 73  # 0x49 given as decimal
    assert b1.dry_raw is None
    assert b1.wet_raw is None


def test_ads1115_probes_malformed_raises(monkeypatch):
    monkeypatch.setenv("ADS1115_PROBES", "not json")
    with pytest.raises(ValueError):
        Config.from_env()


def test_ads1115_probes_bad_channel_raises(monkeypatch):
    monkeypatch.setenv("ADS1115_PROBES", '[{"address":"0x48","channel":7,"sensor_id":"x"}]')
    with pytest.raises(ValueError):
        Config.from_env()


def test_ds18b20_names_parse(monkeypatch):
    monkeypatch.setenv("DS18B20_NAMES", '{"3ce1d4438abc": "basil", "0316a2795e0f": "fig"}')
    cfg = Config.from_env().ds18b20
    assert cfg.names == {"3ce1d4438abc": "basil", "0316a2795e0f": "fig"}


def test_ds18b20_names_malformed_raises(monkeypatch):
    monkeypatch.setenv("DS18B20_NAMES", "not json")
    with pytest.raises(ValueError):
        Config.from_env()
    monkeypatch.setenv("DS18B20_NAMES", '["a-list-not-an-object"]')
    with pytest.raises(ValueError):
        Config.from_env()
    monkeypatch.setenv("DS18B20_NAMES", '{"serial": "  "}')
    with pytest.raises(ValueError):
        Config.from_env()


def test_buffer_spill_path_from_env(monkeypatch):
    monkeypatch.setenv("BUFFER_SPILL_PATH", "/data/spill.db")
    assert Config.from_env().buffer_spill_path == "/data/spill.db"
