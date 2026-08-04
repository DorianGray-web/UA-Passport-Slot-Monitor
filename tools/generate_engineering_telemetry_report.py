"""Generate a local daily, weekly, or monthly AI engineering telemetry audit."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engineering_telemetry import AuditPeriod, SQLiteEngineeringTelemetryStore, write_audit_report

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", choices=[item.value for item in AuditPeriod], required=True)
    parser.add_argument("--at", help="UTC ISO-8601 timestamp; defaults to now")
    parser.add_argument("--database", type=Path, default=PROJECT_ROOT / "data" / "engineering_telemetry.sqlite3")
    parser.add_argument("--output-directory", type=Path, default=PROJECT_ROOT / "reports" / "runtime" / "engineering-telemetry")
    args = parser.parse_args()
    anchor = datetime.fromisoformat(args.at.replace("Z", "+00:00")) if args.at else datetime.now(timezone.utc)
    if anchor.tzinfo is None:
        parser.error("--at must include UTC offset")
    print(write_audit_report(SQLiteEngineeringTelemetryStore(args.database), AuditPeriod(args.period), anchor, args.output_directory))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
