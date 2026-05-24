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
        "HDC302X_ENABLED",
        "HDC302X_ADDRESS",
        "HDC302X_SENSOR_ID",
        "BH1750_ENABLED",
        "BH1750_ADDRESS",
        "BH1750_SENSOR_ID",
        "DS18B20_ENABLED",
        "RESISTIVE_ENABLED",
        "RESISTIVE_GPIO_PIN",
        "RESISTIVE_DRY_WHEN_HIGH",
        "RESISTIVE_SENSOR_ID",
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
