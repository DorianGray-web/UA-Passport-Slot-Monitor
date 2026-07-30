"""Outbox dispatcher that knows only the DispatchTarget contract."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from .event_store import SQLiteEventStore
from .queue import DispatchTarget


class DiagnosticDispatcher:
    def __init__(
        self,
        store: SQLiteEventStore,
        target: DispatchTarget,
    ) -> None:
        self.store = store
        self.target = target

    def dispatch_pending(self, limit: int = 10) -> int:
        delivered = 0
        for record in self.store.pending_outbox(limit):
            try:
                receipt = self.target.dispatch(record.request)
            except Exception as error:
                retry_at = (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=min(2 ** record.attempt, 60))
                ).isoformat()
                self.store.mark_retry(
                    record.outbox_id,
                    retry_at,
                    f"{type(error).__name__}: {error}",
                )
                logging.exception(
                    "Diagnostic dispatch failed. decision_id=%s "
                    "investigation_id=%s",
                    record.decision_id,
                    record.request.investigation_id,
                )
                continue

            # Duplicate/cooldown means the target durably handled the command.
            self.store.mark_delivered(record.outbox_id)
            delivered += 1
            logging.info(
                "Diagnostic dispatch completed. provider=%s event=%s "
                "investigation_id=%s accepted=%s reason=%s",
                record.request.provider_id,
                record.request.event,
                receipt.investigation_id,
                receipt.accepted,
                receipt.reason,
            )
        return delivered
