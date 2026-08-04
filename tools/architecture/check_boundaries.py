"""Fail when static imports or writes cross protected architecture boundaries."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTIFICATION_ROOT = PROJECT_ROOT / "notifications"
TELEMETRY_ROOT = PROJECT_ROOT / "engineering_telemetry"
PROVIDER_ROOT = PROJECT_ROOT / "providers"

FORBIDDEN_NOTIFICATION_IMPORTS = (
    "providers",
    "monitor_runner",
    "diagnostic_worker",
    "diagnostics",
)
FORBIDDEN_PROVIDER_IMPORTS = ("notifications",)
FORBIDDEN_TELEMETRY_IMPORTS = (
    "providers",
    "monitor_runner",
    "diagnostic_worker",
    "diagnostics",
    "notifications",
)
TRUSTED_CONFIGURATION_NAME = "providers.json"


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def render(self) -> str:
        relative = self.path.relative_to(PROJECT_ROOT)
        return f"{relative}:{self.line}: {self.message}"


def python_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return ()
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def imported_modules(tree: ast.AST) -> Iterable[tuple[str, int]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module, node.lineno


def matches_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in prefixes)


def string_literals(node: ast.AST) -> Iterable[str]:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            yield child.value


def assigned_trusted_path_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        if not any(TRUSTED_CONFIGURATION_NAME in value.lower() for value in string_literals(node.value)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def referenced_names(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def write_calls(tree: ast.AST) -> Iterable[ast.Call]:
    write_methods = {"write_text", "write_bytes", "open"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            mode = node.args[1] if len(node.args) > 1 else None
            for keyword in node.keywords:
                if keyword.arg == "mode":
                    mode = keyword.value
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
                if any(flag in mode.value for flag in "wax+"):
                    yield node
        elif isinstance(node.func, ast.Attribute) and node.func.attr in write_methods:
            if node.func.attr != "open":
                yield node
                continue
            mode = node.args[0] if node.args else None
            for keyword in node.keywords:
                if keyword.arg == "mode":
                    mode = keyword.value
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
                if any(flag in mode.value for flag in "wax+"):
                    yield node


def parse(path: Path) -> ast.AST:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise RuntimeError(f"cannot parse {path.relative_to(PROJECT_ROOT)}: {exc}") from exc


def notification_violations() -> list[Violation]:
    violations: list[Violation] = []
    for path in python_files(NOTIFICATION_ROOT):
        tree = parse(path)
        trusted_path_names = assigned_trusted_path_names(tree)
        for module, line in imported_modules(tree):
            if matches_prefix(module, FORBIDDEN_NOTIFICATION_IMPORTS):
                violations.append(
                    Violation(path, line, f"notification code imports protected runtime module {module!r}")
                )
        for call in write_calls(tree):
            literals = tuple(value.lower() for value in string_literals(call))
            direct_path = any(TRUSTED_CONFIGURATION_NAME in value for value in literals)
            indirect_path = bool(referenced_names(call) & trusted_path_names)
            if direct_path or indirect_path:
                violations.append(
                    Violation(path, call.lineno, "notification code writes trusted provider configuration")
                )
    return violations


def provider_violations() -> list[Violation]:
    violations: list[Violation] = []
    for path in python_files(PROVIDER_ROOT):
        tree = parse(path)
        for module, line in imported_modules(tree):
            if matches_prefix(module, FORBIDDEN_PROVIDER_IMPORTS):
                violations.append(
                    Violation(path, line, f"provider code imports output-pipeline module {module!r}")
                )
    return violations


def telemetry_violations() -> list[Violation]:
    violations: list[Violation] = []
    for path in python_files(TELEMETRY_ROOT):
        tree = parse(path)
        for module, line in imported_modules(tree):
            if matches_prefix(module, FORBIDDEN_TELEMETRY_IMPORTS):
                violations.append(
                    Violation(path, line, f"engineering telemetry imports protected project module {module!r}")
                )
    return violations


def main() -> int:
    if not NOTIFICATION_ROOT.is_dir():
        print("No notification package detected. Protected runtime boundaries currently valid.")
    violations = notification_violations() + provider_violations() + telemetry_violations()
    if violations:
        print("Architecture boundary violations:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation.render()}", file=sys.stderr)
        return 1
    print("Architecture boundary guard: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
