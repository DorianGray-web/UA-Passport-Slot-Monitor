"""Replaceable backends used only by the diagnostic worker."""

import logging
import os
from pathlib import Path

from .investigator import (
    DiagnosticBackend,
    InvestigationRequest,
    InvestigationResult,
    SiteInvestigatorBackend,
)


def create_configured_backend() -> DiagnosticBackend | None:
    """Build the selected backend, or disable diagnostics when unconfigured."""
    backend_name = os.getenv("DIAGNOSTIC_BACKEND", "site-investigator").strip()
    if backend_name in {"", "none", "disabled"}:
        return None
    if backend_name != "site-investigator":
        logging.error(
            "Unknown diagnostic backend %r; diagnostics disabled.", backend_name
        )
        return None

    command = os.getenv("SITE_INVESTIGATOR_COMMAND", "").strip()
    if not command:
        return None

    working_directory_value = os.getenv("SITE_INVESTIGATOR_CWD", "").strip()
    working_directory = (
        Path(working_directory_value) if working_directory_value else None
    )
    output_root_value = os.getenv("SITE_INVESTIGATOR_OUTPUT_ROOT", "").strip()
    if output_root_value:
        output_root = Path(output_root_value)
    elif working_directory is not None:
        output_root = working_directory / "research" / "monitor-investigations"
    else:
        logging.error(
            "SITE_INVESTIGATOR_CWD or SITE_INVESTIGATOR_OUTPUT_ROOT is required; "
            "diagnostics disabled to avoid writing artifacts in the monitor."
        )
        return None

    try:
        timeout_seconds = int(
            os.getenv("SITE_INVESTIGATOR_TIMEOUT_SECONDS", "300")
        )
        return SiteInvestigatorBackend(
            command,
            working_directory=working_directory,
            output_root=output_root,
            timeout_seconds=timeout_seconds,
        )
    except (TypeError, ValueError):
        logging.exception(
            "Diagnostic adapter configuration is invalid; diagnostics disabled."
        )
        return None


__all__ = [
    "DiagnosticBackend",
    "InvestigationRequest",
    "InvestigationResult",
    "SiteInvestigatorBackend",
    "create_configured_backend",
]
