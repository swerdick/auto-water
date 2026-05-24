from __future__ import annotations

from ..config import Config
from .base import ReadingSink
from .stdout import StdoutSink


def build_sink(config: Config) -> ReadingSink:
    """Construct the configured sink. Postgres is imported lazily so the
    stdout path (and the test suite) never needs ``psycopg`` installed."""
    if config.sink == "stdout":
        return StdoutSink()
    if config.sink == "postgres":
        if not config.database_url:
            raise ValueError("SINK=postgres requires DATABASE_URL")
        from .postgres import PostgresSink

        return PostgresSink(config.database_url)
    raise ValueError(f"unknown sink: {config.sink!r}")
