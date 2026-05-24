import logging

import pytest

from auto_water.config import Config
from auto_water.models import Reading
from auto_water.sinks import build_sink
from auto_water.sinks.postgres import PostgresSink
from auto_water.sinks.stdout import StdoutSink

# --- build_sink ------------------------------------------------------------


def test_build_sink_stdout():
    assert isinstance(build_sink(Config(sink="stdout")), StdoutSink)


def test_build_sink_postgres_requires_url():
    with pytest.raises(ValueError, match="DATABASE_URL"):
        build_sink(Config(sink="postgres", database_url=None))


def test_build_sink_postgres_returns_sink():
    sink = build_sink(Config(sink="postgres", database_url="postgresql://x/y"))
    assert isinstance(sink, PostgresSink)


def test_build_sink_unknown():
    with pytest.raises(ValueError, match="unknown sink"):
        build_sink(Config(sink="nope"))


# --- StdoutSink ------------------------------------------------------------


def test_stdout_sink_logs_each_reading(caplog):
    sink = StdoutSink()
    with caplog.at_level(logging.INFO, logger="auto_water.sinks.stdout"):
        sink.write([Reading("bh1750", "illuminance", 5.0, "lux")])
    assert "sensor_id=bh1750" in caplog.text
    assert "metric=illuminance" in caplog.text


# --- PostgresSink (with an injected fake connection) -----------------------


class FakeCursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._conn.executed.append(sql)

    def executemany(self, sql, seq):
        if self._conn.fail_executemany:
            raise RuntimeError("write boom")
        self._conn.inserted.extend(seq)


class FakeConnection:
    def __init__(self, fail_executemany=False):
        self.executed = []
        self.inserted = []
        self.commits = 0
        self.closed = False
        self.fail_executemany = fail_executemany

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def _connector(*connections):
    it = iter(connections)

    def connect(_dsn):
        return next(it)

    return connect


def _readings():
    return [
        Reading("env", "temperature", 21.5, "celsius"),
        Reading("env", "humidity", 48.0, "percent"),
    ]


def test_postgres_write_empty_does_not_connect():
    sink = PostgresSink("dsn", connect=_connector())  # no connections available
    sink.write([])  # must not call connect()


def test_postgres_write_inserts_readings():
    conn = FakeConnection()
    sink = PostgresSink("dsn", connect=_connector(conn))
    sink.write(_readings())

    # Schema is owned by migrations now — the sink only inserts, never CREATEs.
    assert not any("CREATE TABLE" in sql for sql in conn.executed)
    assert len(conn.inserted) == 2
    first = conn.inserted[0]
    assert first[:4] == ("env", "temperature", 21.5, "celsius")
    assert first[4] is not None  # recorded_at timestamp passed through
    assert conn.commits >= 1  # the insert is committed


def test_postgres_reconnects_after_failure():
    bad = FakeConnection(fail_executemany=True)
    good = FakeConnection()
    sink = PostgresSink("dsn", connect=_connector(bad, good))

    with pytest.raises(RuntimeError, match="write boom"):
        sink.write(_readings())
    assert bad.closed is True  # broken connection was dropped

    sink.write(_readings())  # should transparently reconnect via `good`
    assert good.closed is False
    assert len(good.inserted) == 2


def test_postgres_close_closes_connection():
    conn = FakeConnection()
    sink = PostgresSink("dsn", connect=_connector(conn))
    sink.write(_readings())
    sink.close()
    assert conn.closed is True
