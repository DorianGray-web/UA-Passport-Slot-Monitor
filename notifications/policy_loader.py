"""Fail-closed loading of versioned notification Policy Sets."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping

from .contracts import require_positive, require_text


__architecture_layer__ = "decision"

IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ROOT_KEYS = {
    "schema_version", "enabled", "policy_sets", "confirmation_policies",
    "deduplication_policies", "priority_policies", "privacy_policies",
    "routing_policies", "provider_overrides",
}
POLICY_KINDS = (
    "confirmation", "deduplication", "priority", "privacy", "routing",
)
POLICY_FIELDS = {
    "confirmation": {
        "policy_version", "minimum_observations", "minimum_duration_seconds",
        "maximum_window_seconds", "required_stage", "required_states",
        "require_consecutive", "reset_states",
    },
    "deduplication": {
        "policy_version", "silence_window_seconds", "aggregation_window_seconds",
        "notify_on_recovery",
    },
    "priority": {"policy_version", "event_priorities"},
    "privacy": {"policy_version", "allowed_fields"},
    "routing": {"policy_version", "routes"},
}


class PolicyConfigurationError(ValueError):
    """Raised when notification policy configuration cannot be trusted."""


@dataclass(frozen=True)
class PolicyReference:
    policy_id: str
    policy_version: int


@dataclass(frozen=True)
class PolicySet:
    policy_set_id: str
    policy_set_version: int
    enabled: bool
    references: Mapping[str, PolicyReference]
    normalized_hash: str

    def reference(self, kind: str) -> PolicyReference:
        try:
            return self.references[kind]
        except KeyError as exc:
            raise PolicyConfigurationError(f"Policy Set has no {kind!r} policy") from exc


@dataclass(frozen=True)
class NotificationPolicyConfiguration:
    schema_version: int
    enabled: bool
    policy_sets: Mapping[str, PolicySet]
    policies: Mapping[str, Mapping[str, Mapping[str, Any]]]
    provider_overrides: Mapping[str, Mapping[str, Any]]
    normalized_hash: str

    def policy_set(self, policy_set_id: str) -> PolicySet:
        try:
            return self.policy_sets[policy_set_id]
        except KeyError as exc:
            raise PolicyConfigurationError(f"Unknown Policy Set {policy_set_id!r}") from exc

    def policy(self, kind: str, reference: PolicyReference) -> Mapping[str, Any]:
        collection = self.policies.get(kind)
        if collection is None:
            raise PolicyConfigurationError(f"Unknown policy kind {kind!r}")
        try:
            policy = collection[reference.policy_id]
        except KeyError as exc:
            raise PolicyConfigurationError(
                f"Unknown {kind} policy {reference.policy_id!r}"
            ) from exc
        if policy["policy_version"] != reference.policy_version:
            raise PolicyConfigurationError(
                f"Version mismatch for {kind} policy {reference.policy_id!r}"
            )
        return policy


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyConfigurationError(f"{name} must be an object")
    return value


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise PolicyConfigurationError(f"{name} is not a valid identifier")
    return value


def _version(value: object, name: str) -> int:
    try:
        require_positive(value, name)  # type: ignore[arg-type]
    except ValueError as exc:
        raise PolicyConfigurationError(str(exc)) from exc
    return value  # type: ignore[return-value]


def _normalized_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _load_reference(value: object, name: str) -> PolicyReference:
    raw = _mapping(value, name)
    if set(raw) != {"policy_id", "policy_version"}:
        raise PolicyConfigurationError(f"{name} has unsupported fields")
    return PolicyReference(
        policy_id=_identifier(raw["policy_id"], f"{name}.policy_id"),
        policy_version=_version(raw["policy_version"], f"{name}.policy_version"),
    )


def _validate_policy(kind: str, policy: dict[str, Any], name: str) -> None:
    if set(policy) != POLICY_FIELDS[kind]:
        raise PolicyConfigurationError(f"{name} has unsupported or missing fields")
    _version(policy["policy_version"], f"{name}.policy_version")
    if kind == "confirmation":
        for field in ("minimum_observations", "maximum_window_seconds"):
            _version(policy[field], f"{name}.{field}")
        duration = policy["minimum_duration_seconds"]
        if isinstance(duration, bool) or not isinstance(duration, int) or duration < 0:
            raise PolicyConfigurationError(f"{name}.minimum_duration_seconds is invalid")
        if policy["required_stage"] not in {"LANDING", "SERVICE_VALIDATION", "DAYS", "TIMES"}:
            raise PolicyConfigurationError(f"{name}.required_stage is invalid")
        for field in ("required_states", "reset_states"):
            values = policy[field]
            if not isinstance(values, list) or (field == "required_states" and not values):
                raise PolicyConfigurationError(f"{name}.{field} is invalid")
            if any(not isinstance(item, str) or not item for item in values) or len(set(values)) != len(values):
                raise PolicyConfigurationError(f"{name}.{field} is invalid")
        if not isinstance(policy["require_consecutive"], bool):
            raise PolicyConfigurationError(f"{name}.require_consecutive is invalid")
    elif kind == "deduplication":
        for field in ("silence_window_seconds", "aggregation_window_seconds"):
            value = policy[field]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise PolicyConfigurationError(f"{name}.{field} is invalid")
        if not isinstance(policy["notify_on_recovery"], bool):
            raise PolicyConfigurationError(f"{name}.notify_on_recovery is invalid")
    elif kind == "priority":
        priorities = _mapping(policy["event_priorities"], f"{name}.event_priorities")
        if any(value not in {"P0", "P1", "P2", "P3"} for value in priorities.values()):
            raise PolicyConfigurationError(f"{name}.event_priorities is invalid")
    elif kind == "privacy":
        fields = policy["allowed_fields"]
        if not isinstance(fields, list) or not fields or len(set(fields)) != len(fields):
            raise PolicyConfigurationError(f"{name}.allowed_fields is invalid")
        for field in fields:
            _identifier(field, f"{name}.allowed_fields item")
    elif kind == "routing":
        routes = policy["routes"]
        if not isinstance(routes, list):
            raise PolicyConfigurationError(f"{name}.routes is invalid")
        route_fields = {
            "profile_id", "enabled", "audience", "channel", "destination_ref",
            "event_types",
        }
        for index, route_value in enumerate(routes):
            route = _mapping(route_value, f"{name}.routes[{index}]")
            if set(route) not in (route_fields, route_fields | {"minimum_priority"}):
                raise PolicyConfigurationError(f"{name}.routes[{index}] has invalid fields")
            _identifier(route["profile_id"], f"{name}.routes[{index}].profile_id")
            if not isinstance(route["enabled"], bool):
                raise PolicyConfigurationError(f"{name}.routes[{index}].enabled is invalid")
            if route["audience"] not in {"developer", "research", "public"}:
                raise PolicyConfigurationError(f"{name}.routes[{index}].audience is invalid")
            if route["channel"] not in {"telegram", "email", "discord", "webhook", "push"}:
                raise PolicyConfigurationError(f"{name}.routes[{index}].channel is invalid")
            destination = route["destination_ref"]
            if not isinstance(destination, str) or re.fullmatch(r"^[A-Z][A-Z0-9_]*$", destination) is None:
                raise PolicyConfigurationError(f"{name}.routes[{index}].destination_ref is invalid")
            events = route["event_types"]
            if not isinstance(events, list) or not events or len(set(events)) != len(events):
                raise PolicyConfigurationError(f"{name}.routes[{index}].event_types is invalid")
            if "minimum_priority" in route and route["minimum_priority"] not in {"P0", "P1", "P2", "P3"}:
                raise PolicyConfigurationError(f"{name}.routes[{index}].minimum_priority is invalid")


def load_policy_configuration(path: str | Path) -> NotificationPolicyConfiguration:
    """Load trusted policy data without enabling delivery or runtime integration."""

    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PolicyConfigurationError(f"Cannot load notification policy configuration: {exc}") from exc
    root = _mapping(raw, "notification configuration")
    missing = ROOT_KEYS - set(root)
    unknown = set(root) - ROOT_KEYS
    if missing or unknown:
        raise PolicyConfigurationError(
            f"Notification configuration fields mismatch; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )
    if root["schema_version"] != 1:
        raise PolicyConfigurationError("Unsupported notification configuration schema_version")
    if not isinstance(root["enabled"], bool):
        raise PolicyConfigurationError("enabled must be boolean")

    collections: dict[str, Mapping[str, Mapping[str, Any]]] = {}
    for kind in POLICY_KINDS:
        collection_name = f"{kind}_policies"
        collection = _mapping(root[collection_name], collection_name)
        checked: dict[str, Mapping[str, Any]] = {}
        for policy_id, value in collection.items():
            _identifier(policy_id, f"{collection_name} key")
            policy = _mapping(value, f"{collection_name}.{policy_id}")
            _validate_policy(kind, policy, f"{collection_name}.{policy_id}")
            checked[policy_id] = _freeze(policy)
        collections[kind] = MappingProxyType(checked)

    policy_sets_raw = _mapping(root["policy_sets"], "policy_sets")
    policy_sets: dict[str, PolicySet] = {}
    for policy_set_id, value in policy_sets_raw.items():
        _identifier(policy_set_id, "policy_set_id")
        policy_set = _mapping(value, f"policy_sets.{policy_set_id}")
        expected = {"enabled", "policy_set_version", *(f"{kind}_policy" for kind in POLICY_KINDS)}
        if set(policy_set) != expected or not isinstance(policy_set["enabled"], bool):
            raise PolicyConfigurationError(f"Invalid Policy Set {policy_set_id!r}")
        references = {
            kind: _load_reference(policy_set[f"{kind}_policy"], f"{policy_set_id}.{kind}_policy")
            for kind in POLICY_KINDS
        }
        loaded = PolicySet(
            policy_set_id=policy_set_id,
            policy_set_version=_version(policy_set["policy_set_version"], "policy_set_version"),
            enabled=policy_set["enabled"],
            references=MappingProxyType(references),
            normalized_hash=_normalized_hash(policy_set),
        )
        for kind, reference in references.items():
            collection = collections[kind]
            if reference.policy_id not in collection:
                raise PolicyConfigurationError(
                    f"Policy Set {policy_set_id!r} references missing {kind} policy"
                )
            if collection[reference.policy_id]["policy_version"] != reference.policy_version:
                raise PolicyConfigurationError(
                    f"Policy Set {policy_set_id!r} references an untrusted {kind} version"
                )
        policy_sets[policy_set_id] = loaded

    overrides = _mapping(root["provider_overrides"], "provider_overrides")
    for provider_id, override_value in overrides.items():
        _identifier(provider_id, "provider override key")
        override = _mapping(override_value, f"provider_overrides.{provider_id}")
        if set(override) != {"confirmation"}:
            raise PolicyConfigurationError(f"provider_overrides.{provider_id} is invalid")
        confirmations = _mapping(override["confirmation"], f"provider_overrides.{provider_id}.confirmation")
        allowed = {
            "minimum_observations", "minimum_duration_seconds",
            "maximum_window_seconds", "require_consecutive",
        }
        for event_type, confirmation_value in confirmations.items():
            require_text(event_type, "provider override event type")
            confirmation = _mapping(confirmation_value, "confirmation override")
            if not confirmation or not set(confirmation) <= allowed:
                raise PolicyConfigurationError("confirmation override has invalid fields")

    return NotificationPolicyConfiguration(
        schema_version=1,
        enabled=root["enabled"],
        policy_sets=MappingProxyType(policy_sets),
        policies=MappingProxyType(collections),
        provider_overrides=_freeze(overrides),
        normalized_hash=_normalized_hash(root),
    )
