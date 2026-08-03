from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import tempfile
import unittest

from notifications.contracts import NotificationCandidate, NotificationEventType, PublicNotificationFacts
from notifications.decisions import NotificationDecisionOutcome
from notifications.policy_loader import PolicyConfigurationError, load_policy_configuration
from notifications.replay import normalized_replay_result, replay


def policy_document() -> dict:
    return {
        "schema_version": 1,
        "enabled": True,
        "policy_sets": {
            "developer-v1": {
                "enabled": True,
                "policy_set_version": 1,
                "confirmation_policy": {"policy_id": "slots-v1", "policy_version": 1},
                "deduplication_policy": {"policy_id": "default-v1", "policy_version": 1},
                "priority_policy": {"policy_id": "default-v1", "policy_version": 1},
                "privacy_policy": {"policy_id": "public-v1", "policy_version": 1},
                "routing_policy": {"policy_id": "developer-v1", "policy_version": 1},
            }
        },
        "confirmation_policies": {
            "slots-v1": {
                "policy_version": 1,
                "minimum_observations": 2,
                "minimum_duration_seconds": 60,
                "maximum_window_seconds": 120,
                "required_stage": "TIMES",
                "required_states": ["SLOTS_AVAILABLE"],
                "require_consecutive": True,
                "reset_states": ["NO_SLOTS", "UNKNOWN", "BLOCKED"],
            }
        },
        "deduplication_policies": {
            "default-v1": {
                "policy_version": 1,
                "silence_window_seconds": 120,
                "aggregation_window_seconds": 120,
                "notify_on_recovery": False,
            }
        },
        "priority_policies": {
            "default-v1": {
                "policy_version": 1,
                "event_priorities": {"SLOTS_AVAILABLE": "P0"},
            }
        },
        "privacy_policies": {
            "public-v1": {
                "policy_version": 1,
                "allowed_fields": ["provider_display_name", "state", "discovery_stage"],
            }
        },
        "routing_policies": {
            "developer-v1": {
                "policy_version": 1,
                "routes": [
                    {
                        "profile_id": "developer-telegram",
                        "enabled": False,
                        "audience": "developer",
                        "channel": "telegram",
                        "destination_ref": "TELEGRAM_DESTINATION",
                        "event_types": ["SLOTS_AVAILABLE"],
                        "minimum_priority": "P0",
                    }
                ],
            }
        },
        "provider_overrides": {},
    }


class NotificationDomainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.config_path = Path(self.temp_directory.name) / "notification_profiles.json"

    def load(self, document: dict | None = None):
        self.config_path.write_text(
            json.dumps(document or policy_document()), encoding="utf-8"
        )
        return load_policy_configuration(self.config_path)

    def candidate(self, *, state: str = "SLOTS_AVAILABLE") -> NotificationCandidate:
        facts = PublicNotificationFacts(
            observed_at="2026-08-03T10:01:00+00:00",
            provider_display_name="Berlin",
            state=state,
            discovery_stage="TIMES",
            available_dates_count=1,
            available_time_slots_count=9,
        )
        return NotificationCandidate(
            candidate_id="NCAND-1",
            event_type=NotificationEventType.SLOTS_AVAILABLE,
            provider_id="dp-document-berlin",
            run_id="RUN-1",
            source_observation_ids=("OBS-1", "OBS-2"),
            first_observed_at="2026-08-03T10:00:00+00:00",
            last_observed_at="2026-08-03T10:01:00+00:00",
            public_facts=facts,
        )

    def test_contracts_are_immutable(self) -> None:
        candidate = self.candidate()
        with self.assertRaises(FrozenInstanceError):
            candidate.candidate_id = "changed"  # type: ignore[misc]

    def test_policy_loader_resolves_versioned_policy_set(self) -> None:
        configuration = self.load()
        policy_set = configuration.policy_set("developer-v1")
        self.assertEqual(1, policy_set.policy_set_version)
        self.assertEqual(64, len(policy_set.normalized_hash))
        with self.assertRaises(TypeError):
            configuration.policy_sets["other"] = policy_set  # type: ignore[index]

    def test_policy_loader_fails_closed_on_unknown_secret_field(self) -> None:
        document = policy_document()
        document["routing_policies"]["developer-v1"]["bot_token"] = "secret"
        with self.assertRaises(PolicyConfigurationError):
            self.load(document)

    def test_confirmation_replay_is_reproducible(self) -> None:
        configuration = self.load()
        first = replay(
            self.candidate(), configuration, "developer-v1",
            decision_id="NDEC-1", decision_trace_id="NTRACE-1",
            evaluation_time="2026-08-03T10:01:30+00:00",
        )
        second = replay(
            self.candidate(), configuration, "developer-v1",
            decision_id="NDEC-2", decision_trace_id="NTRACE-2",
            evaluation_time="2026-08-03T10:01:30+00:00",
        )
        self.assertEqual(normalized_replay_result(first), normalized_replay_result(second))
        self.assertEqual(NotificationDecisionOutcome.ACCEPTED, first.decisions[0].outcome)

    def test_replay_appends_without_mutating_retained_state(self) -> None:
        configuration = self.load()
        first = replay(
            self.candidate(), configuration, "developer-v1",
            decision_id="NDEC-1", decision_trace_id="NTRACE-1",
            evaluation_time="2026-08-03T10:01:30+00:00",
        )
        retained = first.decisions
        second = replay(
            self.candidate(), configuration, "developer-v1", retained,
            decision_id="NDEC-2", decision_trace_id="NTRACE-1",
            evaluation_time="2026-08-03T10:01:30+00:00",
        )
        self.assertEqual(1, len(retained))
        self.assertEqual((1, 2), tuple(item.sequence_number for item in second.decisions))

    def test_confirmation_replay_rejects_mismatched_state(self) -> None:
        trace = replay(
            self.candidate(state="NO_SLOTS"), self.load(), "developer-v1",
            decision_id="NDEC-1", decision_trace_id="NTRACE-1",
            evaluation_time="2026-08-03T10:01:30+00:00",
        )
        self.assertEqual(NotificationDecisionOutcome.REJECTED, trace.decisions[0].outcome)
        self.assertEqual("REQUIRED_FACTS_NOT_MATCHED", trace.decisions[0].reason_code)

    def test_confirmation_replay_expires_outside_window(self) -> None:
        trace = replay(
            self.candidate(), self.load(), "developer-v1",
            decision_id="NDEC-1", decision_trace_id="NTRACE-1",
            evaluation_time="2026-08-03T10:03:00+00:00",
        )
        self.assertEqual(NotificationDecisionOutcome.EXPIRED, trace.decisions[0].outcome)


if __name__ == "__main__":
    unittest.main()
