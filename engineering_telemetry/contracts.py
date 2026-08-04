"""Immutable, privacy-bounded contracts for engineering telemetry."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_FORBIDDEN_TERMS = ("cookie", "csrf", "secret", "token", "password", "prompt", "completion", "otp")

def _text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if any(term in value.lower() for term in _FORBIDDEN_TERMS):
        raise ValueError(f"{field} must not contain sensitive content")

def _identifier(value: str, field: str) -> None:
    _text(value, field)
    if _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{field} must be a compact identifier")

def parse_utc(value: str, field: str) -> datetime:
    _text(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{field} must use UTC")
    return parsed

def _non_negative(value: int | float | None, field: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{field} must be non-negative or null")

class SessionOutcome(str, Enum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass(frozen=True)
class EngineeringSession:
    """Aggregate development facts; never prompts, responses, secrets, or PII."""
    session_id: str
    recorded_at: str
    provider: str
    model: str
    agent: str
    skills: tuple[str, ...]
    workflow_stage: str
    duration_seconds: int
    outcome: SessionOutcome
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    estimated_cost_usd: float | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        for field in ("session_id", "provider", "model", "agent", "workflow_stage"):
            _identifier(getattr(self, field), field)
        parse_utc(self.recorded_at, "recorded_at")
        if isinstance(self.duration_seconds, bool) or not isinstance(self.duration_seconds, int) or self.duration_seconds < 0:
            raise ValueError("duration_seconds must be a non-negative integer")
        if not isinstance(self.skills, tuple):
            raise ValueError("skills must be an immutable tuple")
        for skill in self.skills:
            _identifier(skill, "skills item")
        for field in ("input_tokens", "output_tokens", "cached_tokens", "estimated_cost_usd"):
            _non_negative(getattr(self, field), field)
        if self.schema_version != 1:
            raise ValueError("unsupported EngineeringSession schema_version")

@dataclass(frozen=True)
class EngineeringMetric:
    """Generic quantitative metric for future AI or infrastructure sources."""
    metric_id: str
    recorded_at: str
    source: str
    metric_name: str
    value: float
    unit: str
    session_id: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        for field in ("metric_id", "source", "metric_name", "unit"):
            _identifier(getattr(self, field), field)
        if self.session_id is not None:
            _identifier(self.session_id, "session_id")
        parse_utc(self.recorded_at, "recorded_at")
        _non_negative(self.value, "value")
        if self.schema_version != 1:
            raise ValueError("unsupported EngineeringMetric schema_version")
