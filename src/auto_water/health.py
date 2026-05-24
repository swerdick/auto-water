from __future__ import annotations

import sys
import time
from pathlib import Path


class Heartbeat:
    """A liveness heartbeat backed by a file's modification time.

    The poller calls :meth:`touch` each cycle. The k8s liveness probe runs
    ``python -m auto_water.health`` which exits non-zero when the file is
    stale, so a wedged poll loop (e.g. a blocking I²C read) gets the pod
    restarted instead of silently going quiet.
    """

    def __init__(self, path: str, max_age_seconds: float) -> None:
        self._path = Path(path)
        self._max_age = max_age_seconds

    def touch(self) -> None:
        self._path.touch()

    def is_fresh(self, now: float | None = None) -> bool:
        if not self._path.exists():
            return False
        now = time.time() if now is None else now
        return (now - self._path.stat().st_mtime) <= self._max_age


def _main(argv: list[str] | None = None) -> int:
    from .config import Config

    config = Config.from_env()
    # Allow up to two missed cycles before declaring the pod unhealthy.
    max_age = max(30.0, config.poll_interval_seconds * 2)
    heartbeat = Heartbeat(config.heartbeat_path, max_age)
    return 0 if heartbeat.is_fresh() else 1


if __name__ == "__main__":
    sys.exit(_main())
