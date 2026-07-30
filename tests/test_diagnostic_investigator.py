from __future__ import annotations

import json
import subprocess
import sys
import unittest
from dataclasses import fields
from pathlib import Path
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from diagnostics.investigator import (  # noqa: E402
    InvestigationRequest,
    InvestigationResult,
    SiteInvestigatorBackend,
)


class SiteInvestigatorBackendTests(unittest.TestCase):
    def test_public_result_contract_has_only_documented_fields(self) -> None:
        self.assertEqual(
            tuple(field.name for field in fields(InvestigationResult)),
            (
                "success",
                "investigation_id",
                "exit_code",
                "output_directory",
                "summary",
            ),
        )

    def test_passes_only_request_metadata_to_external_cli(self) -> None:
        backend = SiteInvestigatorBackend(
            ["site-investigator"],
            output_root=Path("external-results"),
        )
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"investigation_id": "inv-123"}),
            stderr="",
        )

        with patch("diagnostics.investigator.subprocess.run", return_value=completed) as run:
            result = backend.investigate(
                InvestigationRequest(
                    url="https://example.test/queue",
                    provider="provider-name",
                    event="BLOCKED",
                )
            )

        command = run.call_args.args[0]
        self.assertEqual(command[:11], [
            "site-investigator",
            "--url",
            "https://example.test/queue",
            "--provider",
            "provider-name",
            "--event",
            "BLOCKED",
            "--mode",
            "research",
            "--investigation-id",
            command[10],
        ])
        self.assertEqual(command[11], "--output")
        self.assertEqual(
            Path(command[12]).parent,
            Path("external-results"),
        )
        self.assertEqual(Path(command[12]).name, command[10])
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.investigation_id, command[10])
        self.assertEqual(
            Path(result.output_directory or "").parent,
            Path("external-results"),
        )

    def test_returns_failure_instead_of_raising_when_cli_is_missing(self) -> None:
        backend = SiteInvestigatorBackend(
            ["missing-site-investigator"],
            output_root=Path("external-results"),
        )
        with patch(
            "diagnostics.investigator.subprocess.run",
            side_effect=FileNotFoundError("not found"),
        ), self.assertLogs(
            "diagnostics.investigator",
            level="ERROR",
        ) as captured:
            result = backend.investigate(
                InvestigationRequest("https://example.test", "provider", "UNKNOWN")
            )

        self.assertFalse(result.success)
        self.assertIsNone(result.exit_code)
        self.assertTrue(result.investigation_id.startswith("INV-"))
        self.assertEqual(
            result.summary,
            "Investigation process failed: FileNotFoundError.",
        )
        self.assertIn("subprocess.run failed.", captured.output[0])
        self.assertIn(
            f"investigation_id={result.investigation_id}",
            captured.output[0],
        )
        self.assertIn("FileNotFoundError: not found", captured.output[0])

    def test_builds_safe_summary_from_capture_quality(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory)
            backend = SiteInvestigatorBackend(
                ["site-investigator"],
                output_root=output_root,
            )

            def complete(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                output_directory = Path(command[command.index("--output") + 1])
                analysis_directory = output_directory / "analysis"
                analysis_directory.mkdir(parents=True)
                (analysis_directory / "capture-quality.json").write_text(
                    json.dumps(
                        {
                            "validTargetPages": 0,
                            "blockedPages": 1,
                            "errorPages": 0,
                            "safeToAnalyze": False,
                            "pages": [
                                {
                                    "url": "https://sensitive.example/path",
                                    "classification": {"blocked": True},
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 0, "Done", "")

            with patch(
                "diagnostics.investigator.subprocess.run",
                side_effect=complete,
            ):
                result = backend.investigate(
                    InvestigationRequest(
                        "https://example.test",
                        "provider",
                        "BLOCKED",
                    )
                )

        self.assertEqual(
            result.summary,
            "Protection or challenge detected; capture is unsafe to analyze.",
        )
        self.assertNotIn("sensitive.example", result.summary or "")


if __name__ == "__main__":
    unittest.main()
