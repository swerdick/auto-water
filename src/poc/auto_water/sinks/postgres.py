from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ..models import Reading
from .base import ReadingSink

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS readings_recorded_at_idx ON readings (recorded_at);
CREATE INDEX IF NOT EXISTS readings_sensor_metric_idx ON readings (sensor_id, metric, recorded_at);
"""

_INSERT = "INSERT INTO readings (sensor_id, metric, value, unit, recorded_at) VALUES (%s, %s, %s, %s, %s)"


def _default_connect(dsn: str) -> Any:
    import psycopg

    return psycopg.connect(dsn)


class PostgresSink(ReadingSink):
    """Writes readings to a Postgres ``readings`` table (a CNPG cluster in prod).

    The connection is created lazily and re-established on demand, so the sink
    rides out the backend going away (e.g. gondor's nightly downtime): a failed
    write drops the connection and re-raises, the poller buffers the batch, and
    the next attempt reconnects and flushes.

    ``connect`` is injectable for testing; the default imports ``psycopg`` lazily.
    """

    def __init__(self, dsn: str, connect: Callable[[str], Any] | None = None) -> None:
        self._dsn = dsn
        self._connect = connect or _default_connect
        self._conn: Any | None = None

    def write(self, readings: list[Reading]) -> None:
        if not readings:
            return
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.executemany(
                    _INSERT,
                    [(r.sensor_id, r.metric, r.value, r.unit, r.recorded_at) for r in readings],
                )
            conn.commit()
        except Exception:
            # Drop the (possibly broken) connection so the next call reconnects.
            self._safe_close()
            raise

    def close(self) -> None:
        self._safe_close()

    def _connection(self) -> Any:
        if self._conn is None or getattr(self._conn, "closed", False):
            self._conn = self._connect(self._dsn)
            self._ensure_schema(self._conn)
        return self._conn

    def _ensure_schema(self, conn: Any) -> None:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA)
        conn.commit()

    def _safe_close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:  # noqa: BLE001
                logger.debug("error closing postgres connection", exc_info=True)
            self._conn = None
