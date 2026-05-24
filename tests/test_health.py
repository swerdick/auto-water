from auto_water.health import Heartbeat, _main


def test_heartbeat_fresh_after_touch(tmp_path):
    path = tmp_path / "hb"
    hb = Heartbeat(str(path), max_age_seconds=100)
    hb.touch()
    assert hb.is_fresh() is True


def test_heartbeat_stale_when_old(tmp_path):
    path = tmp_path / "hb"
    hb = Heartbeat(str(path), max_age_seconds=100)
    hb.touch()
    mtime = path.stat().st_mtime
    assert hb.is_fresh(now=mtime + 50) is True
    assert hb.is_fresh(now=mtime + 200) is False


def test_heartbeat_absent_is_not_fresh(tmp_path):
    hb = Heartbeat(str(tmp_path / "missing"), max_age_seconds=100)
    assert hb.is_fresh() is False


def test_main_returns_zero_when_fresh(tmp_path, monkeypatch):
    path = tmp_path / "hb"
    monkeypatch.setenv("HEARTBEAT_PATH", str(path))
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "10")
    Heartbeat(str(path), 100).touch()
    assert _main() == 0


def test_main_returns_one_when_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("HEARTBEAT_PATH", str(tmp_path / "missing"))
    assert _main() == 1
