# Engineering Telemetry Test Strategy

The telemetry subsystem is tested without network services or AI providers.

1. **Contract tests** validate immutable, UTC, non-negative, privacy-bounded
   records.
2. **Persistence tests** verify append-only SQLite behavior, idempotent record
   IDs, foreign-key integrity, and no-update/no-delete triggers.
3. **Report tests** replay retained local records for deterministic daily,
   weekly, and monthly aggregates.
4. **Architecture tests** ensure telemetry remains independent of monitoring,
   notification, and provider runtime modules.

Reports are aggregates and must be manually reviewed before any sanitized copy
is committed to the repository.
