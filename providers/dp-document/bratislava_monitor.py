from __future__ import annotations

import sys
from pathlib import Path

from city_monitor import CityMonitor, ProviderConfig


MONITOR = CityMonitor(
    ProviderConfig(
        city="Bratislava",
        provider="dp-document-bratislava",
        queue_url="https://bratislava.pasport.org.ua/solutions/e-queue",
        env_prefix="BRATISLAVA",
        base_dir=Path(__file__).resolve().parent,
    )
)


if __name__ == "__main__":
    sys.exit(MONITOR.main())
