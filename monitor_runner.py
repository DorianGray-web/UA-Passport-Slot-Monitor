from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from diagnostics.domain import make_run_id

PROJECT_DIR = Path(__file__).resolve().parent
PROVIDER_DIR = PROJECT_DIR / "providers" / "dp-document"
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "orchestrator.log"
RESTART_DELAY_SECONDS = 10

PROVIDERS = {
    "Kortrijk": PROVIDER_DIR / "kortrijk_monitor.py",
    "Berlin": PROVIDER_DIR / "berlin_monitor.py",
    "Bratislava": PROVIDER_DIR / "bratislava_monitor.py",
}
INFRASTRUCTURE = {
    "Diagnostic worker": PROJECT_DIR / "diagnostic_worker.py",
}


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def start_provider(name: str, script: Path) -> subprocess.Popen[bytes]:
    process = subprocess.Popen(
        [sys.executable, str(script)],
        cwd=PROJECT_DIR,
        env=os.environ.copy(),
    )
    logging.info("%s started (pid=%s)", name, process.pid)
    return process


def stop_all(processes: dict[str, subprocess.Popen[bytes]]) -> None:
    for name, process in processes.items():
        if process.poll() is None:
            process.terminate()
            logging.info("%s stopped", name)
    for process in processes.values():
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def run() -> int:
    run_id = os.getenv("MONITOR_RUN_ID") or make_run_id()
    os.environ["MONITOR_RUN_ID"] = run_id
    processes = {
        name: start_provider(name, script)
        for name, script in {**PROVIDERS, **INFRASTRUCTURE}.items()
    }
    logging.info(
        "Started %s providers and %s diagnostic worker (run_id=%s)",
        len(PROVIDERS),
        len(INFRASTRUCTURE),
        run_id,
    )
    try:
        while True:
            for name, script in {**PROVIDERS, **INFRASTRUCTURE}.items():
                process = processes[name]
                return_code = process.poll()
                if return_code is None:
                    continue
                logging.warning("%s stopped (exit_code=%s)", name, return_code)
                time.sleep(RESTART_DELAY_SECONDS)
                processes[name] = start_provider(name, script)
                logging.info("%s restarted", name)
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Orchestrator stopping")
        stop_all(processes)
        logging.info("Orchestrator stopped")
        return 130


def main() -> int:
    configure_logging()
    return run()


if __name__ == "__main__":
    sys.exit(main())
