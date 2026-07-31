"""HTTP-only DP Document queue-discovery provider.

Confirmed frontend 7.34.2 flow:
Service -> form=days -> form=times.
No browser fingerprint is generated or transmitted by this provider.
"""

from __future__ import annotations

import time
from typing import Any

import requests
from provider_boundaries import (
    DaysRequest,
    MonitorProvider,
    ProviderHTTPResult,
    TimesRequest,
)
from provider_protocol import LandingPageClassifier, LandingPageResult


class DPDocumentHTTPMonitorProvider(MonitorProvider):
    def __init__(
        self,
        *,
        provider_id: str,
        queue_url: str,
        csrf_field: str,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.provider_id = provider_id
        self.queue_url = queue_url
        self.csrf_field = csrf_field
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.landing_classifier = LandingPageClassifier(csrf_field)

    def inspect_landing_page(self) -> LandingPageResult:
        response = self.session.get(
            self.queue_url,
            headers={"Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8"},
            timeout=self.timeout_seconds,
        )
        return self.landing_classifier.classify(
            response.status_code, response.text
        )

    def load_csrf_token(self) -> str:
        result = self.inspect_landing_page()
        if result.csrf_token is None:
            raise ValueError("The DP Document page did not expose a CSRF token.")
        return result.csrf_token

    def _post(self, form: str, fields: dict[str, str]) -> ProviderHTTPResult:
        started = time.perf_counter()
        response = self.session.post(
            self.queue_url,
            data={"form": form, **fields},
            headers={
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=self.timeout_seconds,
        )
        try:
            payload: Any = response.json()
        except ValueError:
            payload = response.text
        return ProviderHTTPResult(
            response.status_code,
            payload,
            round((time.perf_counter() - started) * 1000),
            len(response.content),
        )

    def get_days(self, request: DaysRequest) -> ProviderHTTPResult:
        return self._post(
            "days",
            {
                "ServiceCenterId": request.service_center_id,
                "ServiceId": request.service_id,
                self.csrf_field: request.csrf_token,
            },
        )

    def get_times(self, request: TimesRequest) -> ProviderHTTPResult:
        return self._post(
            "times",
            {
                "ServiceCenterId": request.service_center_id,
                "ServiceId": request.service_id,
                "Date": request.date,
                self.csrf_field: request.csrf_token,
            },
        )
