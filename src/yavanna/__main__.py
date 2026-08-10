from __future__ import annotations

import logging
import signal
from types import FrameType

from .config import Config
from .health import Heartbeat
from .logging_config import configure_logging
from .poller import Poller
from .sensors.factory import build_sensors
from .sinks import build_sink
from .spill import SpillStore


def main() -> None:
    config = Config.from_env()
    configure_logging(config.log_level)
    logger = logging.getLogger("yavanna")

    sensors = build_sensors(config)
    sink = build_sink(config)
    heartbeat = Heartbeat(config.heartbeat_path, max(30.0, config.poll_interval_seconds * 2))

    spill = SpillStore(config.buffer_spill_path) if config.buffer_spill_path else None

    poller = Poller(
        sensors,
        sink,
        interval=config.poll_interval_seconds,
        heartbeat=heartbeat,
        buffer_max=config.buffer_max,
        retention_seconds=config.buffer_retention_days * 86400,
        spill=spill,
    )

    def _handle_signal(signum: int, _frame: FrameType | None) -> None:
        logger.info("received signal %s, shutting down", signum)
        poller.stop()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    poller.run()


if __name__ == "__main__":
    main()
