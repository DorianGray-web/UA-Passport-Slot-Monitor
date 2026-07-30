from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from diagnostics import InvestigationRequest, create_configured_backend
from diagnostics.dispatcher import DiagnosticDispatcher
from diagnostics.domain import QueueJobError
from diagnostics.event_store import SQLiteEventStore
from diagnostics.queue import SQLiteDiagnosticQueue


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("MONITOR_DATA_DIR", PROJECT_DIR / "data"))
LOG_DIR = Path(os.getenv("MONITOR_LOG_DIR", PROJECT_DIR / "logs"))
EVENT_STORE_PATH = Path(
    os.getenv("OBSERVATION_STORE_PATH", DATA_DIR / "observations.sqlite3")
)
QUEUE_PATH = Path(
    os.getenv("DIAGNOSTIC_QUEUE_PATH", DATA_DIR / "diagnostic-queue.sqlite3")
)
LEASE_SECONDS = int(os.getenv("DIAGNOSTIC_LEASE_SECONDS", "300"))
POLL_SECONDS = float(os.getenv("DIAGNOSTIC_WORKER_POLL_SECONDS", "2"))
WORKER_ID = os.getenv(
    "DIAGNOSTIC_WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}"
)


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "diagnostic-worker.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run() -> int:
    event_store = SQLiteEventStore(EVENT_STORE_PATH)
    queue = SQLiteDiagnosticQueue(QUEUE_PATH)
    dispatcher = DiagnosticDispatcher(event_store, queue)
    backend = create_configured_backend()
    if backend is None:
        logging.warning(
            "Diagnostic backend is disabled; dispatcher and worker are idle."
        )

    while True:
        dispatcher.dispatch_pending()
        if backend is not None:
            job = queue.claim(WORKER_ID, LEASE_SECONDS)
            if job is not None:
                logging.info(
                    "Diagnostic job started. provider=%s event=%s "
                    "investigation_id=%s attempt=%s",
                    job.request.provider_id,
                    job.request.event,
                    job.investigation_id,
                    job.attempt,
                )
                try:
                    result = backend.investigate(
                        InvestigationRequest(
                            url=job.request.url,
                            provider=job.request.provider_id,
                            event=job.request.event,
                            mode=job.request.mode,
                            investigation_id=job.investigation_id,
                        )
                    )
                except Exception as error:
                    retry_at = (
                        datetime.now(timezone.utc) + timedelta(minutes=1)
                    ).isoformat()
                    queue.fail(
                        job.investigation_id,
                        job.lease_token,
                        QueueJobError(type(error).__name__, str(error), True),
                        retry_at,
                    )
                    logging.exception(
                        "Diagnostic job failed. investigation_id=%s",
                        job.investigation_id,
                    )
                else:
                    queue.complete(
                        job.investigation_id,
                        job.lease_token,
                        result,
                    )
                    logging.info(
                        "Diagnostic job completed. investigation_id=%s success=%s",
                        job.investigation_id,
                        result.success,
                    )
        time.sleep(POLL_SECONDS)


def main() -> int:
    configure_logging()
    try:
        return run()
    except KeyboardInterrupt:
        logging.info("Diagnostic worker stopped manually.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
