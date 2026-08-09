from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime

from .models import Reading

logger = logging.getLogger(__name__)


class SpillStore:
    """SQLite-backed mirror of the poller's in-memory retry buffer.

    Durability contract: after every cycle the spill file holds exactly the
    readings the in-memory buffer holds, so a pod restart mid-outage reloads
    them instead of dropping them. In the healthy steady state the buffer is
    empty and the spill sees **zero writes** — flash wear is bounded to outage
    windows, which is what lets this run on samwise's SD card ahead of the
    USB-SSD swap.

    Every method is failure-tolerant: a broken spill (full/corrupt disk)
    degrades to the old in-memory-only behavior with loud logs rather than
    taking down live sensing.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        # Skip the DELETE on the success path unless something might be stored;
        # keeps healthy cycles at zero SQLite operations.
        self._may_have_rows = False
        self._conn: sqlite3.Connection | None = None
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            self._conn = sqlite3.connect(path)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS spill ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " sensor_id TEXT NOT NULL,"
                " metric TEXT NOT NULL,"
                " value REAL NOT NULL,"
                " unit TEXT NOT NULL,"
                " recorded_at TEXT NOT NULL)"
            )
            self._conn.commit()
        except (sqlite3.Error, OSError):
            logger.exception(
                "spill store unavailable at %s; buffering in memory only", path
            )
            self._conn = None

    def load(self) -> list[Reading]:
        """Return spilled readings (oldest first) left by a previous process.

        Rows stay in the file — the loader owns them now and clear() removes
        them after the first successful sink write, so a crash between load
        and flush can't lose them.
        """
        if self._conn is None:
            return []
        try:
            rows = self._conn.execute(
                "SELECT sensor_id, metric, value, unit, recorded_at"
                " FROM spill ORDER BY id"
            ).fetchall()
        except sqlite3.Error:
            logger.exception("failed to load spill from %s; starting empty", self._path)
            return []
        if rows:
            self._may_have_rows = True
            logger.info(
                "restored %d spilled reading(s) from %s (previous outage survived a restart)",
                len(rows),
                self._path,
            )
        return [
            Reading(sensor_id, metric, value, unit, datetime.fromisoformat(recorded_at))
            for sensor_id, metric, value, unit, recorded_at in rows
        ]

    def append(self, readings: list[Reading]) -> None:
        """Mirror one failed cycle's new readings (one INSERT batch + commit)."""
        if self._conn is None or not readings:
            return
        try:
            self._conn.executemany(
                "INSERT INTO spill (sensor_id, metric, value, unit, recorded_at)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    (r.sensor_id, r.metric, r.value, r.unit, r.recorded_at.isoformat())
                    for r in readings
                ],
            )
            self._conn.commit()
            self._may_have_rows = True
        except sqlite3.Error:
            logger.exception("failed to spill %d reading(s) to %s", len(readings), self._path)

    def prune(self, cutoff: datetime, max_rows: int) -> None:
        """Match the in-memory bounds: drop rows older than the retention
        cutoff, then oldest rows beyond the count cap."""
        if self._conn is None or not self._may_have_rows:
            return
        try:
            self._conn.execute(
                "DELETE FROM spill WHERE recorded_at < ?", (cutoff.isoformat(),)
            )
            self._conn.execute(
                "DELETE FROM spill WHERE id NOT IN"
                " (SELECT id FROM spill ORDER BY id DESC LIMIT ?)",
                (max_rows,),
            )
            self._conn.commit()
        except sqlite3.Error:
            logger.exception("failed to prune spill at %s", self._path)

    def clear(self) -> None:
        """Empty the spill after a successful sink write. No-op (zero SQLite
        operations) when nothing was ever spilled."""
        if self._conn is None or not self._may_have_rows:
            return
        try:
            self._conn.execute("DELETE FROM spill")
            self._conn.commit()
            self._may_have_rows = False
        except sqlite3.Error:
            logger.exception("failed to clear spill at %s", self._path)

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:  # pragma: no cover - close() failures are inert
                pass
            self._conn = None
