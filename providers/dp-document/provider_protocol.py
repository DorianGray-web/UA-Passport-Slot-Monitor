"""Evidence-first state-machine contracts shared by provider implementations."""

from __future__ import annotations

import json
from datetime import date, datetime
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
    SERVICE_SELECTOR_FOUND = "SERVICE_SELECTOR_FOUND"
    SERVICE_OPTIONS_FOUND = "SERVICE_OPTIONS_FOUND"
    DATE_SELECTOR_FOUND = "DATE_SELECTOR_FOUND"
    TIME_SELECTOR_FOUND = "TIME_SELECTOR_FOUND"
    CANDIDATE_EVIDENCE_PROBE = "CANDIDATE_EVIDENCE_PROBE"
    AUTH_REQUIRED_MARKER = "AUTH_REQUIRED_MARKER"
    MAINTENANCE_MARKER = "MAINTENANCE_MARKER"
    CHALLENGE_MARKER = "CHALLENGE_MARKER"
    UNRECOGNIZED_HTML = "UNRECOGNIZED_HTML"
    AVAILABLE_DATES_FOUND = "AVAILABLE_DATES_FOUND"
    NO_AVAILABLE_DATES = "NO_AVAILABLE_DATES"
    AVAILABLE_TIMES_FOUND = "AVAILABLE_TIMES_FOUND"
    NO_AVAILABLE_TIMES = "NO_AVAILABLE_TIMES"
    DAYS_PAYLOAD_UNRECOGNIZED = "DAYS_PAYLOAD_UNRECOGNIZED"
    TIMES_PAYLOAD_UNRECOGNIZED = "TIMES_PAYLOAD_UNRECOGNIZED"


@dataclass(frozen=True, slots=True)
class QueueForm:
    service_center_id: str | None
    service_id: str | None


@dataclass(frozen=True, slots=True)
class CandidateServiceOption:
    service_id: str
    label: str


@dataclass(frozen=True, slots=True)
class CandidateQueueForm:
    service_center_id: str | None
    options: tuple[CandidateServiceOption, ...]
    date_selector_found: bool
    time_selector_found: bool


@dataclass(frozen=True, slots=True)
class LandingPageResult:
    state: LandingState
    csrf_token: str | None
    queue_form: QueueForm | None
    evidence: tuple[EvidenceCode, ...]


@dataclass(frozen=True, slots=True)
class DaysResult:
    dates: tuple[str, ...]
    evidence: tuple[EvidenceCode, ...]
    recognized: bool


@dataclass(frozen=True, slots=True)
class TimesResult:
    times: tuple[str, ...]
    evidence: tuple[EvidenceCode, ...]
    recognized: bool


class ConfirmedDaysClassifier:
    """Strict classifier for the confirmed DP Document `days` schema."""

    _FIELDS = {"datePart", "date", "isAllowed"}

    def classify(self, status_code: int, payload: object) -> DaysResult:
        if status_code != 200 or not isinstance(payload, dict):
            return self._unknown()
        if set(payload) != {"days"} or not isinstance(payload["days"], list):
            return self._unknown()

        dates: list[str] = []
        for item in payload["days"]:
            if not isinstance(item, dict) or set(item) != self._FIELDS:
                return self._unknown()
            date_part = item["datePart"]
            display_date = item["date"]
            allowed = item["isAllowed"]
            if (
                not isinstance(date_part, str)
                or not isinstance(display_date, str)
                or type(allowed) is not bool
            ):
                return self._unknown()
            try:
                parsed = date.fromisoformat(date_part)
                rendered = datetime.strptime(display_date, "%d.%m.%Y").date()
            except ValueError:
                return self._unknown()
            if parsed != rendered:
                return self._unknown()
            if allowed:
                dates.append(date_part)

        evidence = (
            EvidenceCode.AVAILABLE_DATES_FOUND
            if dates
            else EvidenceCode.NO_AVAILABLE_DATES
        )
        return DaysResult(tuple(dates), (EvidenceCode.HTTP_200, evidence), True)

    @staticmethod
    def _unknown() -> DaysResult:
        return DaysResult(
            (), (EvidenceCode.DAYS_PAYLOAD_UNRECOGNIZED,), False
        )


class ConfirmedTimesClassifier:
    """Strict classifier for the confirmed DP Document `times` schema."""

    _FIELDS = {"startTime", "slot", "isAllowed"}

    def classify(self, status_code: int, payload: object) -> TimesResult:
        if status_code != 200 or not isinstance(payload, dict):
            return self._unknown()
        if (
            set(payload) != {"timeSlots"}
            or not isinstance(payload["timeSlots"], list)
        ):
            return self._unknown()

        times: list[str] = []
        for item in payload["timeSlots"]:
            if not isinstance(item, dict) or set(item) != self._FIELDS:
                return self._unknown()
            start_time = item["startTime"]
            slot = item["slot"]
            allowed = item["isAllowed"]
            if (
                not isinstance(start_time, str)
                or not isinstance(slot, str)
                or type(allowed) is not bool
            ):
                return self._unknown()
            try:
                parsed = datetime.strptime(start_time, "%H:%M:%S")
            except ValueError:
                return self._unknown()
            normalized = parsed.strftime("%H:%M:%S")
            if normalized != start_time or not slot.startswith(start_time[:5]):
                return self._unknown()
            if allowed:
                times.append(start_time)

        evidence = (
            EvidenceCode.AVAILABLE_TIMES_FOUND
            if times
            else EvidenceCode.NO_AVAILABLE_TIMES
        )
        return TimesResult(tuple(times), (EvidenceCode.HTTP_200, evidence), True)

    @staticmethod
    def _unknown() -> TimesResult:
        return TimesResult(
            (), (EvidenceCode.TIMES_PAYLOAD_UNRECOGNIZED,), False
        )


class LandingPageClassifier:
    """Classify landing HTML before any days/times transition is allowed."""

    NO_SLOTS_PHRASES = (
        "Наразі всі місця зайняті",
        "Будь ласка, спробуйте в інший час або день",
    )
    BLOCKING_CHALLENGE_MARKERS = (
        "checking your browser",
        "verify you are human",
        "перевірка безпеки",
        "cf-chl-",
        "/cdn-cgi/challenge-platform/",
        'id="challenge-form"',
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
        embedded = self._embedded_queue_config(soup)
        centre = (
            self._field_value(soup, "ServiceCenterId")
            or self._field_value(soup, "center")
            or self._string_value(embedded.get("center"))
        )
        service = (
            self._field_value(soup, "ServiceId")
            or self._field_value(soup, "service")
        )
        service_selector = soup.select_one(
            'select[name="service"], select[name="ServiceId"]'
        )
        service_options = self._candidate_service_options(service_selector)
        date_selector = soup.select_one(
            'select[name="date"], select[name="Date"]'
        )
        time_selector = soup.select_one(
            'select[name="time"], select[name="Time"]'
        )
        form = soup.select_one("form")
        if form is not None:
            evidence.append(EvidenceCode.QUEUE_FORM_FOUND)
        if csrf:
            evidence.append(EvidenceCode.CSRF_FOUND)
        if centre:
            evidence.append(EvidenceCode.SERVICE_CENTER_FOUND)
        if service:
            evidence.append(EvidenceCode.SERVICE_FOUND)
        if service_selector is not None:
            evidence.append(EvidenceCode.SERVICE_SELECTOR_FOUND)
        if service_options:
            evidence.append(EvidenceCode.SERVICE_OPTIONS_FOUND)
        if date_selector is not None:
            evidence.append(EvidenceCode.DATE_SELECTOR_FOUND)
        if time_selector is not None:
            evidence.append(EvidenceCode.TIME_SELECTOR_FOUND)

        if form is not None and csrf:
            return LandingPageResult(
                LandingState.DISCOVERY_READY,
                csrf,
                QueueForm(centre, service),
                tuple(evidence),
            )
        if any(
            marker in lowered for marker in self.BLOCKING_CHALLENGE_MARKERS
        ):
            evidence.append(EvidenceCode.CHALLENGE_MARKER)
            return LandingPageResult(
                LandingState.BLOCKED, None, None, tuple(evidence)
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
        embedded = self._embedded_queue_config(soup)
        return self._string_value(embedded.get("csrf"))

    @classmethod
    def confirmed_public_form_csrf_field(
        cls,
        html: str,
        *,
        service_center_id: str,
        service_id: str,
    ) -> str | None:
        """Return the opaque field only for an explicitly confirmed form."""
        soup = BeautifulSoup(html, "html.parser")
        embedded = cls._embedded_queue_config(soup)
        centre = cls._string_value(embedded.get("center"))
        service = soup.select_one(
            f'select[name="service"] option[value="{service_id}"]'
        )
        csrf_field = cls._string_value(embedded.get("csrf"))
        if (
            centre != service_center_id
            or service is None
            or csrf_field is None
        ):
            return None
        return csrf_field

    @classmethod
    def confirmed_public_browser_form(
        cls,
        html: str,
        *,
        service_center_id: str,
        service_id: str,
    ) -> bool:
        """Validate browser-rendered public selectors without reading CSRF."""
        soup = BeautifulSoup(html, "html.parser")
        embedded = cls._embedded_queue_config(soup)
        centre = (
            cls._field_value(soup, "ServiceCenterId")
            or cls._field_value(soup, "center")
            or cls._string_value(embedded.get("center"))
        )
        service = soup.select_one(
            f'select[name="service"] option[value="{service_id}"]'
        )
        date_select = soup.select_one(
            'select[name="date"], select[name="Date"]'
        )
        return (
            centre == service_center_id
            and service is not None
            and date_select is not None
        )

    @classmethod
    def public_browser_form_identifiers(
        cls, html: str
    ) -> tuple[str, str] | None:
        """Return unambiguous public centre/service identifiers or fail closed."""
        soup = BeautifulSoup(html, "html.parser")
        embedded = cls._embedded_queue_config(soup)
        centre = (
            cls._field_value(soup, "ServiceCenterId")
            or cls._field_value(soup, "center")
            or cls._string_value(embedded.get("center"))
        )
        services = {
            str(option.get("value"))
            for option in soup.select('select[name="service"] option[value]')
            if str(option.get("value") or "").strip()
        }
        date_select = soup.select_one(
            'select[name="date"], select[name="Date"]'
        )
        if centre and len(services) == 1 and date_select is not None:
            return centre, services.pop()
        return None

    @classmethod
    def candidate_public_form(cls, html: str) -> CandidateQueueForm | None:
        """Extract public landing-form candidates without reading secrets."""
        soup = BeautifulSoup(html, "html.parser")
        selector = soup.select_one(
            'select[name="service"], select[name="ServiceId"]'
        )
        if selector is None or selector.find_parent("form") is None:
            return None
        embedded = cls._embedded_queue_config(soup)
        centre = (
            cls._field_value(soup, "ServiceCenterId")
            or cls._field_value(soup, "center")
            or cls._string_value(embedded.get("center"))
        )
        return CandidateQueueForm(
            service_center_id=centre,
            options=cls._candidate_service_options(selector),
            date_selector_found=soup.select_one(
                'select[name="date"], select[name="Date"]'
            )
            is not None,
            time_selector_found=soup.select_one(
                'select[name="time"], select[name="Time"]'
            )
            is not None,
        )

    @staticmethod
    def _candidate_service_options(
        selector: object | None,
    ) -> tuple[CandidateServiceOption, ...]:
        if selector is None or not hasattr(selector, "select"):
            return ()
        options: list[CandidateServiceOption] = []
        for option in selector.select("option[value]"):
            value = str(option.get("value") or "").strip()
            if not value:
                continue
            label = " ".join(option.get_text(" ", strip=True).split())
            options.append(CandidateServiceOption(value, label))
        return tuple(options)

    @staticmethod
    def _embedded_queue_config(soup: BeautifulSoup) -> dict[str, object]:
        for element in soup.select("[x-data]"):
            value = str(element.get("x-data") or "").strip()
            prefix = "qlogicFormTotoro("
            if not value.startswith(prefix) or not value.endswith(")"):
                continue
            try:
                payload = json.loads(value[len(prefix) : -1])
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(payload, dict):
                return payload
        return {}

    @staticmethod
    def _string_value(value: object) -> str | None:
        if value is None:
            return None
        rendered = str(value)
        return rendered if rendered else None
        return None

    @staticmethod
    def _field_value(soup: BeautifulSoup, name: str) -> str | None:
        element = soup.select_one(f'[name="{name}"]')
        if element is None:
            return None
        value = element.get("value")
        if value is None and element.name == "select":
            selected = element.select_one("option[selected]")
            if selected is not None:
                value = selected.get("value")
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
