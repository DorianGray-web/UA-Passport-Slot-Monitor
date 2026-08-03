"""Check tracked files for runtime artifacts and high-confidence secrets."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_DIRECTORY_NAMES = {
    ".browser-data",
    "analysis",
    "artifacts",
    "captures",
    "cookies",
    "credentials",
    "csrf-snapshots",
    "local-storage",
    "logs",
    "metadata",
    "network",
    "observations",
    "playwright",
    "research-output",
    "screenshots",
    "secrets",
    "session-storage",
    "storage",
    "tokens",
}
FORBIDDEN_SUFFIXES = {
    ".db",
    ".har",
    ".jsonl",
    ".key",
    ".log",
    ".pem",
    ".pyc",
    ".session",
    ".sqlite",
    ".sqlite3",
    ".trace",
}
FORBIDDEN_EXACT_NAMES = {".env", "storage-state.json", "storage_state.json"}
FORBIDDEN_NAME_PATTERNS = (
    re.compile(r"^\.env\."),
    re.compile(r"csrf[-_]snapshot", re.IGNORECASE),
    re.compile(r"storage[-_]state", re.IGNORECASE),
    re.compile(r"-playwright-fallback-.*-report\.md$", re.IGNORECASE),
)

SCANNED_SUFFIXES = {".cfg", ".ini", ".json", ".py", ".ps1", ".toml", ".txt", ".yaml", ".yml"}
DOCUMENTATION_ROOTS = {"docs", "plans", "research", "specs"}
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Telegram bot token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def tracked_files() -> list[PurePosixPath]:
    result = git("ls-files", "-z")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return [PurePosixPath(item) for item in result.stdout.split("\0") if item]


def artifact_reason(path: PurePosixPath) -> str | None:
    lowered_parts = tuple(part.lower() for part in path.parts)
    if lowered_parts and lowered_parts[0] == "data":
        return "runtime-data directory"
    if any(part in FORBIDDEN_DIRECTORY_NAMES for part in lowered_parts):
        return "runtime-artifact directory"
    if any(
        lowered_parts[index : index + 2] == ("reports", "runtime")
        for index in range(max(0, len(lowered_parts) - 1))
    ):
        return "runtime-report directory"
    name = path.name.lower()
    if name in FORBIDDEN_EXACT_NAMES or any(pattern.search(name) for pattern in FORBIDDEN_NAME_PATTERNS):
        return "runtime state or local environment file"
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return "generated/runtime file extension"
    return None


def secret_scan_targets(paths: Iterable[PurePosixPath]) -> Iterable[PurePosixPath]:
    for path in paths:
        if path.parts and path.parts[0].lower() in DOCUMENTATION_ROOTS:
            continue
        if path.suffix.lower() in SCANNED_SUFFIXES or path.name in {"requirements.txt"}:
            yield path


def secret_findings(paths: Iterable[PurePosixPath]) -> list[str]:
    findings: list[str] = []
    for path in secret_scan_targets(paths):
        full_path = PROJECT_ROOT.joinpath(*path.parts)
        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(f"{path}: cannot inspect tracked text file: {exc}")
            continue
        for label, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append(f"{path}:{line}: possible {label}")
    return findings


def worktree_findings() -> list[str]:
    result = git("status", "--porcelain", "--untracked-files=all")
    if result.returncode:
        return [result.stderr.strip() or "git status failed"]
    return [f"working tree is not clean: {line}" for line in result.stdout.splitlines() if line]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-worktree",
        action="store_true",
        help="also fail when tracked or untracked files changed during the CI job",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        paths = tracked_files()
    except RuntimeError as exc:
        print(f"Repository hygiene check failed: {exc}", file=sys.stderr)
        return 1

    findings = [
        f"{path}: {reason}"
        for path in paths
        if (reason := artifact_reason(path)) is not None
    ]
    findings.extend(secret_findings(paths))
    if args.check_worktree:
        findings.extend(worktree_findings())

    if findings:
        print("Repository hygiene violations:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1

    suffix = " and clean worktree" if args.check_worktree else ""
    print(f"Repository hygiene guard: PASS ({len(paths)} tracked files{suffix})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
