from auto_water.models import Reading
from auto_water.poller import Poller
from auto_water.sensors.base import SensorError


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
    reading = _reading()
    sink = FakeSink()
    hb = FakeHeartbeat()
    poller = Poller([FakeSensor("s", [reading])], sink, interval=0.0, heartbeat=hb)
    poller.poll_once()
    assert sink.batches == [[reading]]
    assert hb.touches == 1


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


def test_buffer_is_bounded():
    sink = FakeSink(fail_times=100)
    poller = Poller([FakeSensor("s", [_reading()])], sink, interval=0.0, heartbeat=FakeHeartbeat(), buffer_max=3)
    for _ in range(10):
        poller.poll_once()
    # Internal buffer never exceeds the cap even though every write failed.
    assert len(poller._buffer) == 3  # noqa: SLF001 - asserting the bound directly


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
