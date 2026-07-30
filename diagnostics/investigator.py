"""External-process adapter for optional Site Investigator diagnostics.

This module deliberately knows nothing about Site Investigator internals. The
configured command is treated as an external CLI and receives only non-sensitive
request metadata. Site Investigator remains responsible for all browser state
and diagnostic artifacts.
"""

from __future__ import annotations

import json
import logging
import shlex
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, Sequence


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InvestigationRequest:
    url: str
    provider: str
    event: str
    mode: str = "research"
    investigation_id: str = field(default_factory=lambda: new_investigation_id())


@dataclass(frozen=True, slots=True)
class InvestigationResult:
    success: bool
    investigation_id: str
    exit_code: int | None
    output_directory: str
    summary: str


def new_investigation_id() -> str:
    return (
        f"INV-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-"
        f"{uuid.uuid4().hex[:8]}"
    )


class DiagnosticBackend(Protocol):
    """Replaceable boundary used by monitors to request an investigation."""

    def investigate(self, request: InvestigationRequest) -> InvestigationResult:
        """Run one diagnostic investigation and return process metadata."""


def _summarize_capture(output_directory: Path) -> str:
    """Return a coarse, non-sensitive summary of Site Investigator output."""
    capture_quality_file = (
        output_directory / "analysis" / "capture-quality.json"
    )
    try:
        payload = json.loads(capture_quality_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return "No capture-quality summary was produced."
    if not isinstance(payload, dict):
        return "No capture-quality summary was produced."

    blocked_pages = payload.get("blockedPages", 0)
    error_pages = payload.get("errorPages", 0)
    valid_pages = payload.get("validTargetPages", 0)
    safe_to_analyze = payload.get("safeToAnalyze") is True

    if blocked_pages and not safe_to_analyze:
        return "Protection or challenge detected; capture is unsafe to analyze."
    if blocked_pages:
        return "Protection or challenge detected on one or more pages."
    if error_pages and not valid_pages:
        return "Capture failed before a valid target page was collected."
    if safe_to_analyze:
        return "Target pages captured and marked safe to analyze."
    return "Investigation completed without a conclusive capture summary."


class SiteInvestigatorBackend:
    """Invoke a configured Site Investigator CLI without importing its code."""

    def __init__(
        self,
        command: str | Sequence[str],
        *,
        working_directory: Path | None = None,
        output_root: Path,
        timeout_seconds: int = 300,
    ) -> None:
        if isinstance(command, str):
            self._command = tuple(shlex.split(command, posix=False))

            logging.info("Configured command: %r", self._command)
            logging.info("Command types: %r", [type(x).__name__ for x in self._command])
        else:
            self._command = tuple(command)
        if not self._command:
            raise ValueError("Site Investigator command must not be empty.")
        self._working_directory = working_directory
        self._output_root = output_root
        self._timeout_seconds = timeout_seconds

    def investigate(self, request: InvestigationRequest) -> InvestigationResult:
        requested_id = request.investigation_id
        output_directory = self._output_root / requested_id
        command = [
            *self._command,
            "--url",
            request.url,
            "--provider",
            request.provider,
            "--event",
            request.event,
            "--mode",
            request.mode,
            "--investigation-id",
            requested_id,
        ]
        command.extend(["--output", str(output_directory)])

        logging.info("Executing command: %r", command)
        logging.info("Working directory: %r", self._working_directory)
        logging.info("Output directory: %r", output_directory)
        logging.info(
            "Working directory exists: %s",
            (
                self._working_directory.exists()
                if self._working_directory is not None
                else "not_configured"
            ),
        )
        logging.info(
            "package.json exists: %s",
            (
                (self._working_directory / "package.json").exists()
                if self._working_directory is not None
                else "not_configured"
            ),
        )
        
        try:
            completed = subprocess.run(
                command,
                cwd=self._working_directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            LOGGER.exception(
                "subprocess.run failed. investigation_id=%s",
                requested_id,
            )
            stdout = getattr(error, "stdout", "") or ""
            stderr = getattr(error, "stderr", "") or ""
            return InvestigationResult(
                success=False,
                investigation_id=requested_id,
                exit_code=None,
                output_directory=str(output_directory),
                summary=f"Investigation process failed: {type(error).__name__}.",
            )

        return InvestigationResult(
            success=completed.returncode == 0,
            investigation_id=requested_id,
            exit_code=completed.returncode,
            output_directory=str(output_directory),
            summary=_summarize_capture(output_directory),
        )
