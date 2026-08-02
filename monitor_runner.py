from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from diagnostics.domain import make_run_id

PROJECT_DIR = Path(__file__).resolve().parent
PROVIDER_DIR = PROJECT_DIR / "providers" / "dp-document"
if str(PROVIDER_DIR) not in sys.path:
    sys.path.insert(0, str(PROVIDER_DIR))

from provider_registry import RegisteredProvider, load_provider_registry

LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "orchestrator.log"
RESTART_DELAY_SECONDS = 10
SUMMARY_GENERATOR = (
    PROJECT_DIR
    / "research"
    / "dp-document"
    / "tools"
    / "generate_research_summary.py"
)

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


def configured_providers() -> dict[str, RegisteredProvider]:
    providers = {
        provider.monitor.city: provider
        for provider in load_provider_registry().values()
        if provider.enabled
    }
    selected_value = os.getenv("MONITOR_PROVIDER_CITIES", "").strip()
    if not selected_value:
        return providers
    selected = {
        city.strip().casefold()
        for city in selected_value.split(",")
        if city.strip()
    }
    known = {name.casefold(): name for name in providers}
    unknown = sorted(selected.difference(known))
    if unknown:
        raise ValueError(
            "Unknown or disabled provider cities: " + ", ".join(unknown)
        )
    return {
        name: provider
        for name, provider in providers.items()
        if name.casefold() in selected
    }


def configured_run_duration_seconds() -> float | None:
    value = os.getenv("MONITOR_RUN_DURATION_SECONDS", "").strip()
    if not value:
        return None
    duration = float(value)
    if duration <= 0:
        raise ValueError("MONITOR_RUN_DURATION_SECONDS must be positive")
    return duration


def start_provider(
    name: str,
    script: Path,
    *,
    extra_env: dict[str, str] | None = None,
) -> subprocess.Popen[bytes]:
    environment = os.environ.copy()
    if extra_env:
        environment.update(extra_env)
    process = subprocess.Popen(
        [sys.executable, str(script)],
        cwd=PROJECT_DIR,
        env=environment,
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


def generate_research_summary(
    run_id: str,
    *,
    run_started_at: datetime,
    run_ended_at: datetime,
) -> Path | None:
    enabled = os.getenv("RESEARCH_SUMMARY_ENABLED", "true")
    if enabled.strip().lower() not in {"1", "true", "yes", "on"}:
        logging.info("Research summary generation is disabled")
        return None
    command = [
        sys.executable,
        str(SUMMARY_GENERATOR),
        "--run-id",
        run_id,
        "--minimum-duration-hours",
        os.getenv("RESEARCH_SUMMARY_MINIMUM_HOURS", "1"),
        "--run-started-at",
        run_started_at.isoformat(),
        "--run-ended-at",
        run_ended_at.isoformat(),
    ]
    output_dir = os.getenv("RESEARCH_SUMMARY_OUTPUT_DIR", "").strip()
    if output_dir:
        command.extend(["--output-dir", output_dir])
    completed = subprocess.run(
        command,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    message = completed.stdout.strip()
    if completed.returncode == 0 and message:
        report = Path(message.splitlines()[-1])
        logging.info("Research summary generated: %s", report)
        return report
    if completed.returncode == 3:
        logging.info("Research summary skipped: %s", message)
        return None
    logging.warning(
        "Research summary generation failed (exit_code=%s): %s",
        completed.returncode,
        completed.stderr.strip() or message or "no details",
    )
    return None


def run() -> int:
    run_started_at = datetime.now(timezone.utc)
    run_duration_seconds = configured_run_duration_seconds()
    deadline = (
        time.monotonic() + run_duration_seconds
        if run_duration_seconds is not None
        else None
    )
    run_id = os.getenv("MONITOR_RUN_ID") or make_run_id()
    os.environ["MONITOR_RUN_ID"] = run_id
    providers = configured_providers()
    provider_scripts = {
        name: provider.entrypoint for name, provider in providers.items()
    }
    processes = {
        name: start_provider(
            name,
            provider.entrypoint,
            extra_env={
                "PROVIDER_INITIAL_DELAY_SECONDS": str(
                    provider.startup_delay_seconds
                )
            },
        )
        for name, provider in providers.items()
    }
    processes.update(
        {
            name: start_provider(name, script)
            for name, script in INFRASTRUCTURE.items()
        }
    )
    for name, provider in providers.items():
        logging.info(
            "%s research configuration: priority=%s observation_group=%s "
            "startup_delay_seconds=%s",
            name,
            provider.priority,
            provider.observation_group,
            provider.startup_delay_seconds,
        )
    logging.info(
        "Started %s providers and %s diagnostic worker (run_id=%s)",
        len(providers),
        len(INFRASTRUCTURE),
        run_id,
    )
    if run_duration_seconds is not None:
        logging.info(
            "Bounded monitoring duration: %.0f seconds",
            run_duration_seconds,
        )
    try:
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                run_ended_at = datetime.now(timezone.utc)
                logging.info("Bounded monitoring duration reached")
                logging.info("Orchestrator stopping")
                stop_all(processes)
                generate_research_summary(
                    run_id,
                    run_started_at=run_started_at,
                    run_ended_at=run_ended_at,
                )
                logging.info("Orchestrator stopped")
                return 0
            for name, script in {**provider_scripts, **INFRASTRUCTURE}.items():
                process = processes[name]
                return_code = process.poll()
                if return_code is None:
                    continue
                logging.warning("%s stopped (exit_code=%s)", name, return_code)
                time.sleep(RESTART_DELAY_SECONDS)
                provider = providers.get(name)
                processes[name] = start_provider(
                    name,
                    script,
                    extra_env=(
                        {
                            "PROVIDER_INITIAL_DELAY_SECONDS": str(
                                provider.startup_delay_seconds
                            )
                        }
                        if provider is not None
                        else None
                    ),
                )
                logging.info("%s restarted", name)
            time.sleep(1)
    except KeyboardInterrupt:
        run_ended_at = datetime.now(timezone.utc)
        logging.info("Orchestrator stopping")
        stop_all(processes)
        generate_research_summary(
            run_id,
            run_started_at=run_started_at,
            run_ended_at=run_ended_at,
        )
        logging.info("Orchestrator stopped")
        return 130


def main() -> int:
    configure_logging()
    return run()


if __name__ == "__main__":
    sys.exit(main())
