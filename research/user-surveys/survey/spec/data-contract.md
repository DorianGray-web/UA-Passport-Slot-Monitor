# Survey data contract

**Contract name:** survey_response
**Contract version:** 2.0.0
**Survey version:** 1.0.0
**Canonical source:** survey_web_form
**Status:** normative specification; schema implementation available at
`shared/schemas/survey-response.schema.json`

## Scope and compatibility

This contract connects the web form and client JavaScript to any conforming
backend adapter and later anonymized processing. Google Apps Script and Google
Sheets are candidate adapter/storage consumers only. Stable identifiers and
English canonical field names are authoritative. Localized labels never cross
the transport boundary.

The current shared/schemas/survey-response.schema.json implements the
survey_response/2.0.0 contract. Earlier singular-centre or unversioned schema
drafts are historical context and must not be used for new survey
submissions. The schema and shared taxonomy files must remain version-aligned
with this contract before the form is deployed.

## Submission envelope

The client sends one JSON object:

    {
      "response_id": "550e8400-e29b-41d4-a716-446655440000",
      "survey_version": "1.0.0",
      "contract_version": "2.0.0",
      "source": "survey_web_form",
      "locale": "uk",
      "submitted_at": "2026-08-20T16:42:31.123Z",
      "answers": {
        "residence_region_id": "eu",
        "centre_ids": ["berlin", "munich"],
        "other_centre_text": null,
        "service_id": "international_passport",
        "other_service_text": null,
        "slot_search_experience": "searching_now",
        "check_frequency": "daily",
        "search_duration": "one_to_4_weeks",
        "appointment_urgency": "within_1_month",
        "problem_category_ids": [],
        "other_problem_text": null,
        "cross_border_flexibility": "maybe",
        "notification_channel_ids": ["telegram"],
        "other_notification_channel_text": null,
        "primary_notification_channel_id": "telegram",
        "manual_captcha_attitude": "acceptable_if_rare",
        "early_testing_interest": "yes",
        "additional_context": null
      },
      "consent": {
        "research": true
      },
      "client": {
        "timezone_offset_minutes": 120
      }
    }

Rules:

- response_id is a client-generated UUID v4 from a cryptographically secure
  random source. It has no relationship to identity and is the idempotency key.
- submitted_at is generated at final submission in ISO 8601 UTC with Z.
- source must equal survey_web_form.
- locale is uk, ru, or en; it records UI language, not nationality.
- answers contains only fields defined below.
- centre_ids contains canonical research IDs, never labels or numeric provider
  service_center_id values.
- consent.research must be true.
- client metadata is optional and restricted to timezone_offset_minutes.
- Do not collect or store IP, precise location, User-Agent, referrer, cookies,
  fingerprint, advertising ID, hidden identifiers, or raw browser telemetry.

## Field dictionary

Candidate storage columns in this table record the existing Google Sheets
mapping proposal and are adapter-specific, not `SurveyResponse v2` fields.
Required means the field path must exist in JSON. Nullable fields exist with
JSON null when unanswered or inactive. Arrays default to an empty array.

### Envelope and consent

| Path | Type; required; nullable | Cardinality / enum / default | Validation and maximum | Source and candidate storage column | Analytics and migration |
| --- | --- | --- | --- | --- | --- |
| response_id | string; yes; no | 1 UUID; no default | UUID v4 canonical lowercase; 36 chars | Client; response_id | Deduplication only; preserve |
| survey_version | string; yes; no | 1 semver; 1.0.0 | Exact supported version; max 20 | Client config; survey_version | Questionnaire cohort; preserve |
| contract_version | string; yes; no | 1 semver; 2.0.0 | Exact supported major; max 20 | Client config; contract_version | Parser routing; preserve |
| source | string; yes; no | survey_web_form | Exact enum; max 40 | Client config; source | Source separation; never coerce to social-listening |
| locale | string; yes; no | uk, ru, en | Exact enum; max 2 | Client UI; locale | Language QA; map legacy locale aliases explicitly |
| submitted_at | string; yes; no | 1 UTC timestamp | RFC 3339 profile, millisecond precision accepted, terminal Z; max 30 | Client; submitted_at_client_utc | Submission cohort; retain raw client time |
| consent.research | boolean; yes; no | true | Reject false or absent | User; consent_research | Processing gate; never backfill true |
| client.timezone_offset_minutes | integer; no; yes | -840 through 840; null | Whole minutes only | Browser Date API; timezone_offset_minutes | Coarse UX analysis only; drop if future review finds no need |

A candidate backend adapter may add `server_received_at_utc` and
`processing_status` to its storage representation after separate approval.
They are adapter-specific server metadata, not client-writable envelope fields.

### Answers

| Path | Type; required; nullable | Cardinality / enum / default | Validation and maximum | Source and candidate storage column | Analytics and migration |
| --- | --- | --- | --- | --- | --- |
| answers.residence_region_id | string; yes; no | eu, united_kingdom, canada, other_country | Exact enum; max 32 | Q residence_region; residence_region_id | Coarse residence segment; map old labels by versioned table |
| answers.centre_ids | array of strings; yes; no | 1-5 unique taxonomy IDs; no default | Known IDs or system other_centre/not_decided; exclusivity enforced | Q desired_centres; centre_ids_json | Centre demand; normalize legacy values without overwriting raw |
| answers.other_centre_text | string; yes; yes | null unless other_centre selected | Trim 2-80; no controls, URL or email | Q other_centre_text; other_centre_text | Taxonomy review; redact before publication |
| answers.service_id | string; yes; no | international_passport, id_card, passport_exchange, id_and_passport, other | Exact enum; max 32 | Q document_service; service_id | Service demand; normalize historical labels |
| answers.other_service_text | string; yes; yes | null unless service_id is other | Trim 2-80; no controls, URL or email | Q other_service_text; other_service_text | Taxonomy review |
| answers.slot_search_experience | string; yes; no | not_started, searching_now, searched_before, booked_before | Exact enum; max 24 | Q slot_search_experience; slot_search_experience | Experience cohort; new field is null only in imported legacy rows |
| answers.check_frequency | string; yes; no | several_times_daily, daily, several_times_weekly, occasionally, not_checking_yet | Exact enum; max 32 | Q check_frequency; check_frequency | Search burden; normalize historical labels |
| answers.search_duration | string; yes; yes | under_1_week, one_to_4_weeks, one_to_3_months, over_3_months, not_sure; null | Exact enum | Q search_duration; search_duration | Duration band; legacy null means not asked |
| answers.appointment_urgency | string; yes; yes | within_2_weeks, within_1_month, within_3_months, later, not_sure; null | Exact enum | Q appointment_urgency; appointment_urgency | Urgency band; legacy null means not asked |
| answers.problem_category_ids | array of strings; yes; no | 0-5 unique taxonomy IDs; [] | Known IDs; other and none exclusive as specified | Q problem_categories; problem_category_ids_json | Problem distribution; old free text remains in legacy raw field |
| answers.other_problem_text | string; yes; yes | null unless other selected | Trim 2-160; no controls, URL or email | Q other_problem_text; other_problem_text | Manual coding only; no verbatim chart labels |
| answers.cross_border_flexibility | string; yes; yes | yes, maybe, no, not_sure; null | Exact enum | Q cross_border_flexibility; cross_border_flexibility | Multi-country product need; legacy null means not asked |
| answers.notification_channel_ids | array of strings; yes; no | 1-3 unique taxonomy IDs | Known IDs; other and none exclusive | Q notification_channels; notification_channel_ids_json | Channel demand; normalize push label aliases |
| answers.other_notification_channel_text | string; yes; yes | null unless other selected | Trim 2-80; reject URL, email, phone and handle patterns | Q other_notification_channel_text; other_notification_channel_text | Taxonomy review, not contact collection |
| answers.primary_notification_channel_id | string; yes; no | One selected channel ID | Must be in notification_channel_ids, except reviewed other flow | Q primary_notification_channel; primary_notification_channel_id | Primary channel |
| answers.manual_captcha_attitude | string; yes; no | acceptable, acceptable_if_rare, require_full_automation, not_sure | Exact enum; max 32 | Q manual_captcha_attitude; manual_captcha_attitude | UX expectation only; grants no bypass authority |
| answers.early_testing_interest | string; yes; no | yes, no, maybe | Exact enum | Q early_testing_interest; early_testing_interest | Recruitment interest aggregate only; no contact |
| answers.additional_context | string; yes; yes | null or text | Trim; maximum 500; no control chars | Q additional_context; additional_context | Restricted qualitative review; never publish verbatim |

## Enum and reference ownership

| Value family | Single owner | Consumer rule |
| --- | --- | --- |
| Centres, countries, macro regions, aliases | shared/taxonomy/centres.json | Form and processor load the same versioned artifact |
| Problem categories | shared/taxonomy/problem-categories.json | Do not duplicate IDs in question config |
| Notification channels | shared/taxonomy/notification-channels.json | Primary channel must reference the same IDs |
| Survey-only enums | This contract | Client constants are generated or checked against contract tests |
| Localized labels | Translation configuration | Labels never become stored values |

A centre record separates centre_id, country_code, macro_region_id, localized
label keys, legacy aliases, and optional provider_service_center_id. Dynamic
availability classifications do not belong in the centre record.

The canonical survey taxonomies are populated and versioned. Centres, problem
categories, and notification channels must be loaded from their respective
files and validated against the declared taxonomy snapshots before deployment.
These survey taxonomies are separate from the runtime provider registry and do
not assert operational provider support or current slot availability. `munich`
is a valid survey centre even though it is not currently represented as an
operational runtime provider. A null or unavailable
`provider_service_center_id` must not exclude a valid centre from the survey
taxonomy. Munich may later become an operational runtime provider when the
required provider identifiers and evidence become available.


Channel IDs and their non-runtime status are also governed by
[Notification Channel Survey Research](notification-channels.md). A survey
answer records preference only and never creates a notification subscription.
## Transport and persistence boundary

This document owns the canonical `survey_response/2.0.0` object, its field
meaning, versioning, schema relationship, and taxonomy references. It does not
select or define a production transport, backend adapter, or storage platform.

The adapter-neutral operation, semantic outcomes, validation boundary,
idempotency model, privacy constraints, failure matrix, and OPEN production
decisions are proposed in
[Survey transport and persistence contract](transport-persistence.md) and
[ADR-0014](../../../../docs/DECISIONS.md#adr-0014-survey-submission-transport-and-persistence-boundary).

The preserved outcomes are `ACCEPTED`, `DUPLICATE_ACCEPTED`,
`INVALID_REQUEST`, `UNSUPPORTED_CONTRACT`, and `TEMPORARY_FAILURE`. HTTP method,
media type, response encoding, status mapping, timeout, retry, CORS, allowed
origins, retention, deletion, deployment, and infrastructure logging remain
OPEN until separately approved.

No secret, API key, spreadsheet ID, privileged token, deployment URL, or
private deployment configuration may be committed or embedded in client
JavaScript.

## Candidate Google Apps Script and Google Sheets adapter profile

> **Status: Adapter-specific candidate; not an accepted production contract.**
>
> This section records a possible first storage mapping. It does not authorize
> Apps Script deployment, Google Sheets persistence, locking, retry, timeout,
> CORS, retention, deletion, or logging. Feasibility and lifecycle decisions
> remain OPEN.

If Google Sheets is selected after review, a candidate `Responses_v2` sheet
could use fixed ASCII technical headers in this order:

    response_id
    survey_version
    contract_version
    source
    locale
    submitted_at_client_utc
    server_received_at_utc
    consent_research
    timezone_offset_minutes
    residence_region_id
    centre_ids_json
    other_centre_text
    service_id
    other_service_text
    slot_search_experience
    check_frequency
    search_duration
    appointment_urgency
    problem_category_ids_json
    other_problem_text
    cross_border_flexibility
    notification_channel_ids_json
    other_notification_channel_text
    primary_notification_channel_id
    manual_captcha_attitude
    early_testing_interest
    additional_context
    normalization_version
    processing_status

Array columns contain compact JSON arrays, for example ["berlin","munich"].
Do not use comma-separated labels because commas are ambiguous and labels
change. Text cells would require protection from spreadsheet formula execution
in the storage representation. The exact escaping rule, whether any separate
raw value is retained, and all logging behavior require adapter and privacy
review. No access-controlled ingestion log is approved by this document.

Column rules:

- A selected adapter must not localize canonical technical fields or change
  their meaning.
- Storage schema evolution must not redefine contract versioning.
- Append-only behavior, overwrites, deletion, and retention remain OPEN.
- Server-managed fields require explicit approval and are not client-writable
  contract fields.
- Raw Google Sheets exports remain outside Git.

## Adapter-specific legacy import candidate

This historical Google Sheets import proposal is adapter-specific. It does not
select a production datastore or approve retention of legacy/raw material.

Historical rows are imported into a separate Legacy_import sheet or processed
dataset, never mixed silently with native v2 rows. Preserve:

- legacy_source;
- legacy_row_id generated during import;
- legacy_answers_json or scoped raw columns;
- legacy.centre_values_raw;
- normalization_version;
- migration_status;
- migrated_at_utc;
- migration_warnings_json.

Normalized fields are added alongside raw values. Unknown values become
unmapped and remain excluded from category-level analysis until reviewed.
Never infer consent for historical responses. Proposed-addition fields that
did not exist in the old form are null with migration status not_asked, not an
answer such as not_sure.

Cologne, Köln, Кёльн, and Кельн normalize to centre_id cologne under
centre_aliases/1.0.0. Alias matching uses Unicode normalization, trim, and
case-folding, but the original string remains preserved.

## Free text and security

- Maximum lengths: other centre 80, other service 80, other problem 160,
  other channel 80, additional context 500 characters after trim.
- Reject NUL and control characters other than ordinary line breaks in the
  textarea; normalize line endings.
- Treat text as data. Never render with innerHTML and never evaluate it.
- Escape for HTML output and neutralize spreadsheet formula prefixes.
- Do not use free text as a filename, URL, log label, metric label, or query.
- Do not send free text to third-party analytics or AI services by default.
- Review and paraphrase qualitative content before any publication.
- Redact accidental contact, document, and appointment identifiers during
  processing; retain no public verbatim quotation.
- Validation errors use path and stable code only and do not echo rejected text.


Detailed normalization and identifier handling:

- Normalize CRLF and CR to LF; replace non-breaking spaces with ordinary
  spaces; trim leading and trailing whitespace; collapse horizontal whitespace
  runs to one space. Only additional_context may preserve a single LF between
  paragraphs. Single-line fields contain no LF.
- Apply Unicode NFC after whitespace normalization and before length checks.
- HTML is forbidden. Reject markup-like tags rather than trying to sanitize or
  interpret them. Store and process accepted values only as plain text.
- Use textContent or an equivalent safe text API. Never use innerHTML or
  interpolate text into executable HTML, JavaScript, CSS, formulas, or URLs.
- At ingestion, detect likely email addresses, phone numbers, personal-profile
  URLs or handles, document numbers, appointment references, and other direct
  identifiers. Do not echo or log a detected value.
- Reject optional live-form text before storage with error code
  accidental_identifier and ask the respondent to remove the identifier.
- For historical imports that cannot be re-entered, retain raw source only in
  restricted local migration storage outside Git. Store a masked value in
  Sheets or processed data and record redaction_applied and redaction_type.
- Mask email local parts, all but the final two phone digits, personal-profile
  path components, and identifier bodies with [REDACTED]. Keep no reversible
  mapping in survey data.
- A deletion request or confirmed high-risk identifier removes that free-text
  value from processing and records a non-identifying deletion audit status.
  Unrelated structured answers are not rewritten.
- Raw or merely masked text is forbidden in public charts, labels, tooltips,
  downloadable chart data, summaries, and examples. Publish only reviewed
  aggregate codes or non-searchable paraphrases.

## Source separation

This contract applies only to voluntary survey submissions. Public social-media
comments belong under social-listening/ and use the separate
social-observation contract. They are never submitted through this endpoint,
written to Responses_v2, represented as survey answers, or joined row by row
to respondents.

Survey and social-listening visualizations remain separate. Comparative
analysis is allowed only under synthesis/ after each source is independently
processed and normalized to shared taxonomy IDs. Every comparison value must
state source, methodology version, observation period, and sample definition.
Aggregates may be compared; individual survey and social records must not be
linked.
## Versioning and release gates

Semantic versioning applies independently to survey_version, contract_version,
taxonomy versions, and normalization_version.

- PATCH clarifies wording or validation without changing accepted payloads,
  stored meaning, requiredness, branching, or analytical interpretation.
- MINOR adds backward-compatible optional fields or enum values. Old clients
  remain accepted for an explicitly supported minor version; the server never
  invents answers for questions they did not ask.
- MAJOR changes a type, path, requiredness, enum meaning, source semantics, or
  analytical interpretation. It requires a new parser and isolated storage
  representation; a platform-specific tab or table is adapter-owned.
- The backend validation boundary validates the declared version. Unsupported
  clients receive `UNSUPPORTED_CONTRACT` and no accepted persistence side
  effect.
- An old client may continue only while its exact survey and contract versions
  are explicitly supported and tested. Its payload is never interpreted using
  newer semantics silently.
- Historical Google Forms responses retain original source, raw columns,
  question-version evidence, and import timestamp. Normalized fields are
  additive and carry normalization_version and migration status.
- A semantic change creates a new field or major version with documented
  migration and provenance. Quietly changing a field's meaning is forbidden.

Before deployment:

1. Review the populated canonical taxonomies and verify their declared
  versions and ownership.
2. Verify that survey-response.schema.json matches contract 2.0.0.
3. Approve adapter-neutral transport and persistence decisions; do not treat
   an unreviewed or placeholder adapter as compatible.
4. Add contract tests covering every question-field mapping, enum ownership,
   required/nullable behavior, branching, idempotency, formula injection,
   duplicate response_id, and legacy normalization.
5. Verify uk, ru, and en payloads are identical except locale and user choices.
6. For a selected adapter, test the separately approved method, media type,
   outcome mapping, origin, redirect, timeout, and retry behavior in a browser.

No response may enter processed results until its contract, consent, taxonomy,
and normalization versions are known and validation status is accepted.

## Complete examples

The object in Submission envelope is the full valid payload. This is the
minimal valid payload; required nullable paths remain present as null.

~~~json
{
  "response_id": "a26d8b2f-4dbf-4f83-98e4-fc53a277614b",
  "survey_version": "1.0.0",
  "contract_version": "2.0.0",
  "source": "survey_web_form",
  "locale": "en",
  "submitted_at": "2026-08-20T17:00:00Z",
  "answers": {
    "residence_region_id": "other_country",
    "centre_ids": ["not_decided"],
    "other_centre_text": null,
    "service_id": "international_passport",
    "other_service_text": null,
    "slot_search_experience": "not_started",
    "check_frequency": "not_checking_yet",
    "search_duration": null,
    "appointment_urgency": null,
    "problem_category_ids": [],
    "other_problem_text": null,
    "cross_border_flexibility": null,
    "notification_channel_ids": ["email"],
    "other_notification_channel_text": null,
    "primary_notification_channel_id": "email",
    "manual_captcha_attitude": "not_sure",
    "early_testing_interest": "no",
    "additional_context": null
  },
  "consent": {
    "research": true
  }
}
~~~

Each object below is valid JSON but represents invalid submitted data. The
errors member documents expected validation and is not part of the request.

~~~json
[
  {
    "case": "localized centre label and mutually exclusive values",
    "payload": {
      "response_id": "a26d8b2f-4dbf-4f83-98e4-fc53a277614b",
      "answers": {
        "centre_ids": ["Berlin", "not_decided"]
      }
    },
    "errors": [
      {
        "path": "answers.centre_ids[0]",
        "code": "unknown_value"
      },
      {
        "path": "answers.centre_ids",
        "code": "mutually_exclusive"
      }
    ]
  },
  {
    "case": "consent missing and accidental email in text",
    "payload": {
      "response_id": "not-a-uuid",
      "answers": {
        "additional_context": "Contact me at person@example.com"
      }
    },
    "errors": [
      {
        "path": "response_id",
        "code": "invalid_uuid"
      },
      {
        "path": "consent.research",
        "code": "required"
      },
      {
        "path": "answers.additional_context",
        "code": "accidental_identifier"
      }
    ]
  }
]
~~~

Concrete transport response examples are intentionally not defined here. See
[Survey transport and persistence contract](transport-persistence.md) for the
adapter-neutral semantic outcomes. Response encoding and HTTP mapping remain
OPEN adapter/deployment decisions.
