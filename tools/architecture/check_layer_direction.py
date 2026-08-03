"""Protect the one-way dependency direction of the future notification package."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTIFICATION_ROOT = PROJECT_ROOT / "notifications"
LAYER_MARKER = "__architecture_layer__"
LAYERS = {
    "observation": 0,
    "candidate": 1,
    "decision": 2,
    "confirmed_event": 3,
    "queue": 4,
    "adapter": 5,
}

# Markers are authoritative. These names are conservative defaults for the
# proposed package layout and may be extended without changing the algorithm.
CONVENTIONAL_LAYERS = {
    "builder": "candidate",
    "candidate": "candidate",
    "confirmation": "decision",
    "deduplication": "decision",
    "decision": "decision",
    "priority": "decision",
    "privacy": "decision",
    "routing": "decision",
    "confirmed_event": "confirmed_event",
    "events": "confirmed_event",
    "queue": "queue",
    "worker": "queue",
}


@dataclass(frozen=True)
class ModuleInfo:
    path: Path
    module: str
    layer: str | None
    imports: tuple[tuple[str, int], ...]


def module_name(path: Path) -> str:
    relative = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imports(tree: ast.AST, current_module: str, is_package: bool) -> Iterable[tuple[str, int]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            if not node.level:
                if node.module:
                    yield node.module, node.lineno
                    for alias in node.names:
                        yield f"{node.module}.{alias.name}", node.lineno
                continue
            package = current_module.split(".")
            if not is_package:
                package.pop()
            trim = node.level - 1
            if trim:
                package = package[:-trim]
            if node.module:
                package.extend(node.module.split("."))
                yield ".".join(package), node.lineno
            else:
                for alias in node.names:
                    yield ".".join([*package, alias.name]), node.lineno


def declared_layer(tree: ast.Module, path: Path) -> str | None:
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == LAYER_MARKER for target in targets):
            continue
        value = node.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            raise ValueError(f"{path}: {LAYER_MARKER} must be a string literal")
        if value.value not in LAYERS:
            raise ValueError(f"{path}: unsupported architecture layer {value.value!r}")
        return value.value
    return None


def conventional_layer(path: Path) -> str | None:
    if "adapters" in path.relative_to(NOTIFICATION_ROOT).parts:
        return "adapter"
    return CONVENTIONAL_LAYERS.get(path.stem)


def load_modules() -> dict[str, ModuleInfo]:
    modules: dict[str, ModuleInfo] = {}
    for path in sorted(NOTIFICATION_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        name = module_name(path)
        modules[name] = ModuleInfo(
            path=path,
            module=name,
            layer=declared_layer(tree, path) or conventional_layer(path),
            imports=tuple(imports(tree, name, path.name == "__init__.py")),
        )
    return modules


def resolve_import(name: str, modules: dict[str, ModuleInfo]) -> ModuleInfo | None:
    current = name
    while current:
        if current in modules:
            return modules[current]
        current = current.rpartition(".")[0]
    return None


def main() -> int:
    if not NOTIFICATION_ROOT.is_dir():
        print("No notification package detected. Architecture direction currently valid.")
        return 0

    try:
        modules = load_modules()
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        print(f"Notification layer check failed: {exc}", file=sys.stderr)
        return 1

    violations: list[str] = []
    classified = 0
    for source in modules.values():
        if source.layer is None:
            continue
        classified += 1
        source_rank = LAYERS[source.layer]
        for imported_name, line in source.imports:
            target = resolve_import(imported_name, modules)
            if target is None or target.layer is None:
                continue
            if LAYERS[target.layer] > source_rank:
                relative = source.path.relative_to(PROJECT_ROOT)
                violations.append(
                    f"{relative}:{line}: {source.layer} imports downstream "
                    f"{target.layer} module {target.module!r}"
                )

    if violations:
        print("Notification layer direction violations:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print(f"Notification layer direction guard: PASS ({classified} classified modules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
