"""Provider boundaries for monitoring and any separately approved booking work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from provider_protocol import LandingPageResult


@dataclass(frozen=True, slots=True)
class DaysRequest:
    service_center_id: str
    service_id: str
    csrf_token: str


@dataclass(frozen=True, slots=True)
class TimesRequest:
    service_center_id: str
    service_id: str
    date: str
    csrf_token: str


@dataclass(frozen=True, slots=True)
class ProviderHTTPResult:
    status_code: int
    payload: Any
    duration_ms: int = 0
    response_bytes: int = 0


class MonitorProvider(Protocol):
    """Public, pre-authentication availability discovery only."""

    provider_id: str

    def inspect_landing_page(self) -> LandingPageResult:
        ...

    def get_days(self, request: DaysRequest) -> ProviderHTTPResult:
        ...

    def get_times(self, request: TimesRequest) -> ProviderHTTPResult:
        ...


class BookingProvider(Protocol):
    """Reserved boundary for separately approved future booking research.

    Intentionally defines no booking operation. Monitoring code must never
    depend on this interface, browser fingerprint generation, identity,
    authentication, OTP, BankID, Diia, or reservation data.
    """

    provider_id: str
