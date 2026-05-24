from __future__ import annotations

import logging

from ..models import Reading
from .base import ReadingSink

logger = logging.getLogger(__name__)


class StdoutSink(ReadingSink):
    """Logs each reading as a structured line. Used for bench testing without a DB."""

    def write(self, readings: list[Reading]) -> None:
        for r in readings:
            logger.info(
                "reading sensor_id=%s metric=%s value=%s unit=%s at=%s",
                r.sensor_id,
                r.metric,
                r.value,
                r.unit,
                r.recorded_at.isoformat(),
            )
