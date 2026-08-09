import logging
from datetime import UTC, datetime, timedelta

from auto_water.models import Reading
from auto_water.poller import Poller
from auto_water.sensors.base import SensorError
from auto_water.spill import SpillStore


class FakeSensor:
    def __init__(self, sensor_id, readings=None, error=None):
        self.sensor_id = sensor_id
        self._readings = readings or []
        self._error = error

    def read(self):
        if self._error:
            raise self._error
        return list(self._readings)


class FakeSink:
    def __init__(self, fail_times=0):
        self.batches = []
        self.closed = False
        self._fail_times = fail_times

    def write(self, readings):
        if self._fail_times > 0:
            self._fail_times -= 1
            raise RuntimeError("sink down")
        self.batches.append(list(readings))

    def close(self):
        self.closed = True


class FakeHeartbeat:
    def __init__(self):
        self.touches = 0

    def touch(self):
        self.touches += 1


def _reading(sensor_id="s"):
    return Reading(sensor_id, "temperature", 1.0, "celsius")


def _poller(sensors, sink, **kw):
    return Poller(sensors, sink, interval=0.0, heartbeat=FakeHeartbeat(), **kw)


def test_collect_isolates_failing_sensor():
    good = FakeSensor("good", [_reading("good")])
    bad = FakeSensor("bad", error=SensorError("nope"))
    poller = _poller([good, bad, good], FakeSink())
    readings = poller.collect()
    assert len(readings) == 2  # both good reads, bad one skipped
    assert {r.sensor_id for r in readings} == {"good"}


def test_poll_once_writes_and_touches_heartbeat():
    sink = FakeSink()
    hb = FakeHeartbeat()
    poller = Poller([FakeSensor("s", [_reading()])], sink, interval=0.0, heartbeat=hb)
    poller.poll_once()
    # collect() re-stamps each cycle, so compare the stable fields, not identity.
    assert len(sink.batches) == 1
    [written] = sink.batches[0]
    assert (written.sensor_id, written.metric, written.value) == ("s", "temperature", 1.0)
    assert hb.touches == 1


def test_collect_stamps_one_timestamp_per_cycle():
    # Sensors are read sequentially and arrive with different construction times
    # (a slow 1-Wire bus can spread reads over seconds); collect() must collapse
    # the cycle onto a single fresh timestamp so multi-series panels render as
    # continuous lines rather than dots.
    t0 = datetime(2020, 1, 1, tzinfo=UTC)
    a = FakeSensor("a", [Reading("a", "temperature", 1.0, "celsius", recorded_at=t0)])
    b = FakeSensor("b", [Reading("b", "temperature", 2.0, "celsius", recorded_at=t0 + timedelta(seconds=3))])
    readings = _poller([a, b], FakeSink()).collect()
    stamps = {r.recorded_at for r in readings}
    assert len(stamps) == 1  # one cycle → one timestamp
    assert t0 not in stamps  # and it's the cycle's own time, not the sensors'


def test_poll_once_buffers_on_sink_failure_then_flushes():
    sink = FakeSink(fail_times=1)
    hb = FakeHeartbeat()
    poller = Poller([FakeSensor("s", [_reading()])], sink, interval=0.0, heartbeat=hb)

    poller.poll_once()  # sink fails → 1 reading buffered, no batch written
    assert sink.batches == []
    assert hb.touches == 1  # heartbeat still beats even when the sink is down

    poller.poll_once()  # sink recovers → flushes both buffered + new reading
    assert len(sink.batches) == 1
    assert len(sink.batches[0]) == 2


def test_buffer_is_bounded_and_warns_on_drop(caplog):
    sink = FakeSink(fail_times=100)
    poller = Poller([FakeSensor("s", [_reading()])], sink, interval=0.0, heartbeat=FakeHeartbeat(), buffer_max=3)
    with caplog.at_level(logging.WARNING, logger="auto_water.poller"):
        for _ in range(10):
            poller.poll_once()
    # The hard count cap holds even though every write failed.
    assert len(poller._buffer) == 3  # noqa: SLF001 - asserting the bound directly
    # Operators are warned that readings are being discarded.
    assert "hard cap" in caplog.text


def test_buffer_evicts_readings_older_than_retention(caplog):
    # A reading already older than the retention window, sitting in the buffer
    # with the sink down. Injected straight into the buffer: collect() stamps
    # each cycle with a fresh time, so we age the buffer directly here.
    old = Reading("s", "temperature", 1.0, "celsius", recorded_at=datetime.now(UTC) - timedelta(seconds=120))
    sink = FakeSink(fail_times=100)
    poller = Poller([], sink, interval=0.0, heartbeat=FakeHeartbeat(), retention_seconds=60)
    poller._buffer.append(old)  # noqa: SLF001 - seeding the buffer to exercise eviction
    with caplog.at_level(logging.WARNING, logger="auto_water.poller"):
        poller.poll_once()
    # The 2-minute-old reading exceeds the 60s window → evicted, not retained.
    assert len(poller._buffer) == 0  # noqa: SLF001 - asserting the time bound directly
    assert "retention window" in caplog.text


def test_run_stops_and_closes_sink():
    sink = FakeSink()
    poller = _poller([FakeSensor("s", [_reading()])], sink)

    original = poller.poll_once
    polls = []

    def once():
        original()
        polls.append(1)
        poller.stop()

    poller.poll_once = once
    poller.run()

    assert len(polls) == 1
    assert sink.closed is True


def test_run_with_no_sensors_idles_without_error():
    sink = FakeSink()
    poller = _poller([], sink)
    poller.stop()  # stop before entering the loop
    poller.run()
    assert sink.closed is True


# --- durable spill -----------------------------------------------------------


def test_spill_survives_restart_and_flushes(tmp_path):
    path = str(tmp_path / "spill.db")
    sensor = FakeSensor("s", [_reading()])

    # First process: sink down for two cycles → 2 readings in memory AND on disk.
    down = _poller([sensor], FakeSink(fail_times=100), spill=SpillStore(path))
    down.poll_once()
    down.poll_once()
    assert len(SpillStore(path).load()) == 2

    # "Pod restart": a fresh poller on the same file restores the 2 spilled
    # readings, and the first successful write flushes restored + new together.
    sink = FakeSink()
    up = _poller([sensor], sink, spill=SpillStore(path))
    up.poll_once()
    assert len(sink.batches) == 1
    assert len(sink.batches[0]) == 3
    # Flush empties the file — nothing left for a later restart to re-insert.
    assert SpillStore(path).load() == []


def test_spill_untouched_while_sink_healthy(tmp_path):
    path = str(tmp_path / "spill.db")
    poller = _poller([FakeSensor("s", [_reading()])], FakeSink(), spill=SpillStore(path))
    poller.poll_once()
    poller.poll_once()
    assert SpillStore(path).load() == []


def test_spill_prunes_with_retention(tmp_path):
    path = str(tmp_path / "spill.db")
    old = Reading("s", "temperature", 1.0, "celsius", recorded_at=datetime.now(UTC) - timedelta(seconds=120))
    seed = SpillStore(path)
    seed.append([old])
    seed.close()

    # Restart mid-outage: the stale reading is restored, then evicted from
    # memory AND pruned from disk on the next failed cycle.
    poller = _poller(
        [FakeSensor("s", [_reading()])],
        FakeSink(fail_times=100),
        retention_seconds=60,
        spill=SpillStore(path),
    )
    poller.poll_once()
    remaining = SpillStore(path).load()
    assert len(remaining) == 1  # just this cycle's reading; the expired one is gone
    assert remaining[0].recorded_at > datetime.now(UTC) - timedelta(seconds=60)


def test_spill_pruned_to_buffer_cap_at_load(tmp_path, caplog):
    # 5 spilled rows but a 3-slot buffer: the deque keeps the newest 3, and the
    # file must be pruned to the same 3 at load — otherwise a later clear()
    # would discard rows that never made it into memory or the sink.
    path = str(tmp_path / "spill.db")
    seed = SpillStore(path)
    seed.append([_reading(f"s{i}") for i in range(5)])
    seed.close()

    with caplog.at_level(logging.WARNING, logger="auto_water.poller"):
        poller = _poller([], FakeSink(fail_times=100), buffer_max=3, spill=SpillStore(path))
    assert "exceeds the buffer cap" in caplog.text
    assert [r.sensor_id for r in poller._buffer] == ["s2", "s3", "s4"]  # noqa: SLF001
    on_disk = SpillStore(path).load()
    assert [r.sensor_id for r in on_disk] == ["s2", "s3", "s4"]  # disk == memory


def test_broken_spill_degrades_to_memory_only(tmp_path, caplog):
    # A directory as the target path makes sqlite3.connect fail → the store
    # disables itself and the poller runs exactly as before.
    bad_dir = tmp_path / "spill.db"
    bad_dir.mkdir()
    with caplog.at_level(logging.ERROR, logger="auto_water.spill"):
        spill = SpillStore(str(bad_dir))
    assert "spill store unavailable" in caplog.text

    sink = FakeSink(fail_times=1)
    poller = _poller([FakeSensor("s", [_reading()])], sink, spill=spill)
    poller.poll_once()  # fails → buffers in memory, spill no-ops
    poller.poll_once()  # recovers → flushes both readings
    assert len(sink.batches) == 1
    assert len(sink.batches[0]) == 2
