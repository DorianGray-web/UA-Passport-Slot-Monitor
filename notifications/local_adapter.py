"""In-memory delivery adapter for deterministic local worker validation."""

from __future__ import annotations

from .contracts import NotificationDeliveryJob
from .worker import DeliveryResult, DeliveryStatus


__architecture_layer__ = "adapter"


class LocalFakeDeliveryAdapter:
    """Returns configured results and retains attempted immutable jobs in memory only."""

    def __init__(self, results: tuple[DeliveryResult, ...]) -> None:
        if not isinstance(results, tuple):
            raise ValueError("results must be an immutable tuple")
        self._results = results
        self._cursor = 0
        self._attempts: list[NotificationDeliveryJob] = []

    @property
    def attempts(self) -> tuple[NotificationDeliveryJob, ...]:
        return tuple(self._attempts)

    def deliver(
        self,
        job: NotificationDeliveryJob,
    ) -> DeliveryResult:
        self._attempts.append(job)
        if self._cursor >= len(self._results):
            return DeliveryResult(
                status=DeliveryStatus.PERMANENT_FAILURE,
                reason="FAKE_NO_RESULT",
            )
        result = self._results[self._cursor]
        self._cursor += 1
        return result
