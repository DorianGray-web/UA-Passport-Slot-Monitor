from __future__ import annotations

import sys

from city_monitor import CityMonitor
from provider_registry import load_city_provider


MONITOR = CityMonitor(load_city_provider("madrid").monitor)


if __name__ == "__main__":
    sys.exit(MONITOR.main())
