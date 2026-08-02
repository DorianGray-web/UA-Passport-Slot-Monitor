from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from city_monitor import ProviderConfig


PROVIDER_DIR = Path(__file__).resolve().parent
DEFAULT_REGISTRY_PATH = PROVIDER_DIR / "providers.json"
VALID_PRIORITIES = {"normal", "high"}
VALID_OBSERVATION_GROUPS = {"active", "control"}


@dataclass(frozen=True, slots=True)
class RegisteredProvider:
    monitor: ProviderConfig
    entrypoint: Path
    enabled: bool
    priority: str
    observation_group: str
    startup_delay_seconds: int


def load_provider_registry(
    path: Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, RegisteredProvider]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    registered: dict[str, RegisteredProvider] = {}
    for item in payload["providers"]:
        city = str(item["city"]).lower()
        priority = str(item["priority"]).lower()
        observation_group = str(item["research"]["observation_group"]).lower()
        startup_delay_seconds = int(item.get("startup_delay_seconds", 0))
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Unsupported priority for {city}: {priority}")
        if observation_group not in VALID_OBSERVATION_GROUPS:
            raise ValueError(
                f"Unsupported observation group for {city}: {observation_group}"
            )
        if city in registered:
            raise ValueError(f"Duplicate provider city: {city}")
        if startup_delay_seconds < 0:
            raise ValueError(
                f"Startup delay must be non-negative for {city}"
            )
        registered[city] = RegisteredProvider(
            monitor=ProviderConfig(
                city=city.title(),
                provider=str(item["provider"]),
                queue_url=str(item["queue_url"]),
                env_prefix=str(item["env_prefix"]),
                base_dir=PROVIDER_DIR,
                public_discovery_profile=item.get("public_discovery_profile"),
                service_center_id=item.get("service_center_id"),
                service_id=item.get("service_id"),
                csrf_value=item.get("csrf_value"),
                candidate_evidence_probe=bool(
                    item.get("research", {}).get(
                        "candidate_evidence_probe", False
                    )
                ),
            ),
            entrypoint=PROVIDER_DIR / str(item["entrypoint"]),
            enabled=bool(item["enabled"]),
            priority=priority,
            observation_group=observation_group,
            startup_delay_seconds=startup_delay_seconds,
        )
    return registered


def load_city_provider(city: str) -> RegisteredProvider:
    try:
        return load_provider_registry()[city.lower()]
    except KeyError as error:
        raise ValueError(f"Unknown provider city: {city}") from error
