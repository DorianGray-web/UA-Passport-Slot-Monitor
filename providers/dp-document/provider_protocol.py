"""Evidence-first state-machine contracts shared by provider implementations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from bs4 import BeautifulSoup


class LandingState(StrEnum):
    NO_SLOTS = "NO_SLOTS"
    DISCOVERY_READY = "DISCOVERY_READY"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    MAINTENANCE = "MAINTENANCE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class DiscoveryStage(StrEnum):
    LANDING = "LANDING"
    SERVICE_VALIDATION = "SERVICE_VALIDATION"
    DAYS = "DAYS"
    TIMES = "TIMES"


class EvidenceCode(StrEnum):
    HTTP_200 = "HTTP_200"
    HTTP_403 = "HTTP_403"
    HTTP_429 = "HTTP_429"
    HTTP_503 = "HTTP_503"
    HTTP_ERROR = "HTTP_ERROR"
    HTML_NO_SLOTS_MARKER = "HTML_NO_SLOTS_MARKER"
    QUEUE_FORM_FOUND = "QUEUE_FORM_FOUND"
    CSRF_FOUND = "CSRF_FOUND"
    SERVICE_CENTER_FOUND = "SERVICE_CENTER_FOUND"
    SERVICE_FOUND = "SERVICE_FOUND"
    AUTH_REQUIRED_MARKER = "AUTH_REQUIRED_MARKER"
    MAINTENANCE_MARKER = "MAINTENANCE_MARKER"
    CHALLENGE_MARKER = "CHALLENGE_MARKER"
    UNRECOGNIZED_HTML = "UNRECOGNIZED_HTML"


@dataclass(frozen=True, slots=True)
class QueueForm:
    service_center_id: str | None
    service_id: str | None


@dataclass(frozen=True, slots=True)
class LandingPageResult:
    state: LandingState
    csrf_token: str | None
    queue_form: QueueForm | None
    evidence: tuple[EvidenceCode, ...]


class LandingPageClassifier:
    """Classify landing HTML before any days/times transition is allowed."""

    NO_SLOTS_PHRASES = (
        "Наразі всі місця зайняті",
        "Будь ласка, спробуйте в інший час або день",
    )
    CHALLENGE_MARKERS = (
        "captcha",
        "recaptcha",
        "hcaptcha",
        "cloudflare",
        "turnstile",
        "checking your browser",
    )
    AUTH_MARKERS = ("авторизац", "увійдіть", "sign in", "log in")
    MAINTENANCE_MARKERS = (
        "технічні роботи",
        "technical maintenance",
        "temporarily unavailable",
    )

    def __init__(self, csrf_field: str | None = None) -> None:
        self.csrf_field = csrf_field

    def classify(self, status_code: int, html: str) -> LandingPageResult:
        evidence: list[EvidenceCode] = []
        status_evidence = {
            200: EvidenceCode.HTTP_200,
            403: EvidenceCode.HTTP_403,
            429: EvidenceCode.HTTP_429,
            503: EvidenceCode.HTTP_503,
        }.get(status_code)
        if status_evidence is not None:
            evidence.append(status_evidence)

        if status_code in {403, 429, 503}:
            return LandingPageResult(
                LandingState.BLOCKED, None, None, tuple(evidence)
            )
        if status_code >= 400:
            evidence.append(EvidenceCode.HTTP_ERROR)
            return LandingPageResult(
                LandingState.ERROR, None, None, tuple(evidence)
            )

        soup = BeautifulSoup(html, "html.parser")
        normalized = " ".join(soup.get_text(" ", strip=True).split())
        lowered = html.lower()
        if any(marker in lowered for marker in self.CHALLENGE_MARKERS):
            evidence.append(EvidenceCode.CHALLENGE_MARKER)
            return LandingPageResult(
                LandingState.BLOCKED, None, None, tuple(evidence)
            )
        if self.NO_SLOTS_PHRASES[0] in normalized:
            evidence.append(EvidenceCode.HTML_NO_SLOTS_MARKER)
            return LandingPageResult(
                LandingState.NO_SLOTS, None, None, tuple(evidence)
            )
        if any(marker in lowered for marker in self.MAINTENANCE_MARKERS):
            evidence.append(EvidenceCode.MAINTENANCE_MARKER)
            return LandingPageResult(
                LandingState.MAINTENANCE, None, None, tuple(evidence)
            )
        if any(marker in lowered for marker in self.AUTH_MARKERS):
            evidence.append(EvidenceCode.AUTH_REQUIRED_MARKER)
            return LandingPageResult(
                LandingState.AUTH_REQUIRED, None, None, tuple(evidence)
            )

        csrf = self._csrf_token(soup)
        centre = self._field_value(soup, "ServiceCenterId")
        service = self._field_value(soup, "ServiceId")
        form = soup.select_one("form")
        if form is not None:
            evidence.append(EvidenceCode.QUEUE_FORM_FOUND)
        if csrf:
            evidence.append(EvidenceCode.CSRF_FOUND)
        if centre:
            evidence.append(EvidenceCode.SERVICE_CENTER_FOUND)
        if service:
            evidence.append(EvidenceCode.SERVICE_FOUND)

        if form is not None and csrf:
            return LandingPageResult(
                LandingState.DISCOVERY_READY,
                csrf,
                QueueForm(centre, service),
                tuple(evidence),
            )

        evidence.append(EvidenceCode.UNRECOGNIZED_HTML)
        return LandingPageResult(
            LandingState.UNKNOWN, csrf, None, tuple(evidence)
        )

    def _csrf_token(self, soup: BeautifulSoup) -> str | None:
        selectors = ['meta[name="csrf-token"]']
        if self.csrf_field:
            selectors.insert(0, f'input[name="{self.csrf_field}"]')
        for selector in selectors:
            element = soup.select_one(selector)
            if element is not None:
                value = element.get("value") or element.get("content")
                if value:
                    return str(value)
        return None

    @staticmethod
    def _field_value(soup: BeautifulSoup, name: str) -> str | None:
        element = soup.select_one(f'[name="{name}"]')
        if element is None:
            return None
        value = element.get("value")
        return str(value) if value else None


class TransitionGuard:
    """Pure guards prevent unjustified state-machine transitions."""

    @staticmethod
    def allows_days(result: LandingPageResult) -> bool:
        return (
            result.state is LandingState.DISCOVERY_READY
            and result.csrf_token is not None
            and result.queue_form is not None
            and result.queue_form.service_center_id is not None
            and result.queue_form.service_id is not None
        )

    @staticmethod
    def allows_times(*, dates: tuple[str, ...]) -> bool:
        return bool(dates)


class DiscoveryEngine:
    """Provider-neutral transition coordinator.

    Days/times payload interpretation is intentionally outside this class until
    provider response schemas have fixture-backed classifiers.
    """

    def __init__(self, landing_classifier: LandingPageClassifier) -> None:
        self.landing_classifier = landing_classifier

    def classify_landing(
        self, status_code: int, html: str
    ) -> LandingPageResult:
        return self.landing_classifier.classify(status_code, html)

    @staticmethod
    def next_stage_after_landing(
        result: LandingPageResult,
    ) -> DiscoveryStage | None:
        if TransitionGuard.allows_days(result):
            return DiscoveryStage.SERVICE_VALIDATION
        return None

    @staticmethod
    def next_stage_after_days(
        dates: tuple[str, ...],
    ) -> DiscoveryStage | None:
        if TransitionGuard.allows_times(dates=dates):
            return DiscoveryStage.TIMES
        return None
