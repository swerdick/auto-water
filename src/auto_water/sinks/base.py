from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Reading


class ReadingSink(ABC):
    @abstractmethod
    def write(self, readings: list[Reading]) -> None:
        """Persist a batch of readings.

        Must raise on failure so the caller can buffer and retry (the poller
        relies on this to survive the Postgres backend being temporarily gone).
        """

    def close(self) -> None:  # noqa: B027 - optional hook, intentional no-op default
        """Release resources. Default no-op; override if the sink holds any."""
