from __future__ import annotations

import sys
from pathlib import Path

from city_monitor import CityMonitor, ProviderConfig


MONITOR = CityMonitor(
    ProviderConfig(
        city="Berlin",
        provider="dp-document-berlin",
        queue_url="https://berlin.pasport.org.ua/solutions/e-queue",
        env_prefix="BERLIN",
        base_dir=Path(__file__).resolve().parent,
    )
)


if __name__ == "__main__":
    sys.exit(MONITOR.main())
