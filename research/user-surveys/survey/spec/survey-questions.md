# Survey questions

**Status:** implementation specification
**Survey version:** 1.0.0
**Contract:** survey_response/2.0.0
**Locales:** uk, ru, en; English is the fallback

## Purpose and boundaries

This voluntary survey studies Ukrainians outside Ukraine who use, tried to use,
or plan to use Passport Service electronic queues and UA Passport Slot Monitor.
It should establish centre demand, service needs, search burden, notification
preferences, tolerance for manual CAPTCHA hand-off, and willingness to test.

It is not a monitoring UI, subscription manager, booking flow, slot guarantee,
or evidence of current availability. Survey data stays physically separate
from social-listening data. Do not request passport data, appointment numbers,
names, exact addresses, precise location, or unnecessary contact details.

Target completion time is 3-5 minutes. Structured choices are preferred to free
text. All text fields are optional unless activated by an Other choice, are
length-limited, and warn users not to enter personal or document data.

## Evidence from the historical Google Form

The six-page PDF snapshot dated 2026-08-20 was reviewed. It contains 11
questions in Ukrainian. Required questions are residence country, desired
centre, service, check frequency, notification channels, primary channel,
manual CAPTCHA attitude, and early testing willingness. The problem text,
contact, and final comment have no required marker. The PDF shows no section
branching. This specification preserves those research topics while replacing
localized stored values with stable IDs and tightening privacy.

## Form sequence and behavior

1. Introduction, anonymity notice, time estimate, and required research consent.
2. Situation: residence region, service, experience, frequency, and urgency.
3. Centres: multi-select grouped by macro region, country, and city.
4. Problems and product interaction, including manual CAPTCHA hand-off.
5. Notification channel preferences.
6. Testing interest, optional context, review, and submission.

Rules:

- Visible required questions must be valid before continuing.
- Back navigation never clears answers.
- Changing uk, ru, or en rerenders labels without changing answers,
  validation state, current section, or response_id.
- Other reveals a scoped text field. The text is never promoted to an enum ID.
- not_decided is mutually exclusive with concrete centres and other_centre.
- Centre selection permits 1-5 values.
- none is mutually exclusive with notification channels.
- Hidden dependent answers are removed before submission.
- The submit button is disabled while a request is in flight.

## Question registry

Every question uses i18n keys rooted at survey.questions.<question_id>.
The required keys are title, help, error.required, error.invalid, and
options.<option_id> where options exist.

| ID | Source | Control and requirement | Values and branching | Contract field | Analytics and privacy |
| --- | --- | --- | --- | --- | --- |
| research_consent | Proposed addition | Required checkbox | true only | consent.research | Purpose limitation; not charted |
| residence_region | Historical Q1, refined | Required radio | eu, united_kingdom, canada, other_country | answers.residence_region_id | Coarse residence context; never infer from IP |
| desired_centres | Historical Q2 | Required grouped checkbox multi-select | Canonical centre IDs, other_centre, not_decided; 1-5 values | answers.centre_ids | Centre demand; location of desired service, not precise residence |
| other_centre_text | Historical Q2 Other | Required text only when other_centre selected | Trimmed 2-80 characters | answers.other_centre_text | Taxonomy review only; no public verbatim text |
| document_service | Historical Q3 | Required radio | international_passport, id_card, passport_exchange, id_and_passport, other | answers.service_id | Service demand; no passport or case details |
| other_service_text | Historical Q3 Other | Required text only when other selected | Trimmed 2-80 characters | answers.other_service_text | Taxonomy review only |
| slot_search_experience | Proposed addition | Required radio | not_started, searching_now, searched_before, booked_before | answers.slot_search_experience | Separates prospective and experienced cohorts; low burden |
| check_frequency | Historical Q4 | Required radio | several_times_daily, daily, several_times_weekly, occasionally, not_checking_yet | answers.check_frequency | Search burden without browsing history |
| search_duration | Proposed addition | Optional radio; show unless experience is not_started | under_1_week, one_to_4_weeks, one_to_3_months, over_3_months, not_sure | answers.search_duration | Coarse wait duration; no exact dates |
| appointment_urgency | Proposed addition | Optional radio | within_2_weeks, within_1_month, within_3_months, later, not_sure | answers.appointment_urgency | Product prioritization; no sensitive reason |
| problem_categories | Historical Q5 converted from text | Optional checkbox multi-select | Taxonomy IDs, other, none; maximum 5 | answers.problem_category_ids | Structured friction analysis reduces free text |
| other_problem_text | Historical Q5 fallback | Required text only when other selected | Trimmed 2-160 characters | answers.other_problem_text | Manual coding only; never publish verbatim |
| cross_border_flexibility | Proposed addition | Optional radio | yes, maybe, no, not_sure | answers.cross_border_flexibility | Tests multi-country UX; no travel details |
| notification_channels | Historical Q6 | Required checkbox multi-select | Taxonomy IDs, other, none; maximum 3 | answers.notification_channel_ids | Preference only; creates no subscription |
| other_notification_channel_text | Historical Q6 Other | Required when other selected | Trimmed 2-80 characters; channel type only | answers.other_notification_channel_text | Must reject likely contact coordinates |
| primary_notification_channel | Historical Q7 | Required radio | One selected channel ID; other allowed only with Q6 Other | answers.primary_notification_channel_id | Primary channel preference; no address or handle |
| manual_captcha_attitude | Historical Q8 | Required radio | acceptable, acceptable_if_rare, require_full_automation, not_sure | answers.manual_captcha_attitude | Product expectation only; does not authorize CAPTCHA bypass |
| early_testing_interest | Historical Q9 | Required radio | yes, no, maybe | answers.early_testing_interest | Interest measure; must not trigger contact collection |
| additional_context | Historical Q11 | Optional textarea | Trimmed, maximum 500 characters | answers.additional_context | Qualitative coding after review; never publish verbatim |

Channel meaning and governance are further constrained by
[Notification Channel Survey Research](notification-channels.md). That document
does not turn a stated preference into a subscription or runtime configuration.

### Proposed additions assessment

| Question | Research value | Required | Time/burden risk |
| --- | --- | --- | --- |
| research_consent | Explicit voluntary purpose limitation | Yes | Very low |
| slot_search_experience | Separates intended from experienced needs | Yes | Low |
| search_duration | Measures prolonged search friction | No | Low; one conditional choice |
| appointment_urgency | Distinguishes urgent and exploratory demand | No | Low; coarse bands |
| cross_border_flexibility | Tests value of multi-country discovery | No | Low |

Current country of residence is not added as a precise country question in
version 1.0.0 because the historical coarse region answer is sufficient for
initial analysis and lowers re-identification risk. Reconsider only if a
documented decision shows country-level analysis is necessary.

### Contact from historical Q10

Historical Q10 invites Telegram, email, GitHub, or another contact. It is
excluded from the anonymous submission. If follow-up recruitment is approved,
use a separate optional form and datastore with:

- explicit contact consent;
- an independently generated contact_response_id;
- no shared response_id or analytics join key;
- restricted access and a retention deadline;
- exclusion from processed results, summaries, and charts.

## Validation and i18n details

- Enum and taxonomy questions reject unknown IDs.
- Arrays contain unique values and use deterministic taxonomy order.
- other_* text rejects control characters, URLs, email-like strings, phone-like
  strings, and social handles where contact data is not requested.
- additional_context rejects control characters and shows a personal-data
  warning; sanitization never silently changes the research meaning.
- Client validation improves usability. Production ingestion validation is
  defined separately and is not part of the questionnaire contract.
- Localized labels are never submitted.
- Required error keys follow survey.questions.<id>.error.required.
- Invalid-value keys follow survey.questions.<id>.error.invalid.
- Length keys follow survey.questions.<id>.error.length.
- Global keys cover navigation, the privacy notice, and generic submission
  progress and result messaging. Production transport behavior is defined
  separately and is not part of the questionnaire contract.

## Canonical service-centre catalogue

The single owner is shared/taxonomy/centres.json. The UI must derive the list
from it and must not copy this table into JavaScript. The catalogue is
populated and versioned independently from the runtime provider registry.
`munich` is a valid survey centre even though it is not currently represented
as an operational runtime provider. A null or unavailable
`provider_service_center_id` must not exclude a valid centre from the survey
taxonomy. Munich may later become an operational runtime provider when the
required provider identifiers and evidence become available.

For configured deployments, the research centre_id equals the existing
providers.json city slug. The numeric provider service_center_id remains a
separate integration identifier and is never the survey answer.

| Macro region | Country | City | centre_id | Existing provider ID |
| --- | --- | --- | --- | --- |
| Schengen Area | Germany, DE | Berlin | berlin | 2 |
| Schengen Area | Germany, DE | Cologne | cologne | 3 |
| Schengen Area | Germany, DE | Munich | munich | Not currently represented as an operational runtime provider |
| Schengen Area | Slovakia, SK | Bratislava | bratislava | 9 |
| Schengen Area | Belgium, BE | Kortrijk | kortrijk | 48 |
| Schengen Area | Spain, ES | Madrid | madrid | 6 |
| Schengen Area | Spain, ES | Barcelona | barcelona | 41 |
| Schengen Area | Spain, ES | Valencia | valencia | 7 |
| Schengen Area | Italy, IT | Milan | milan | 4 |
| Schengen Area | Czechia, CZ | Prague | prague | 8 |
| Schengen Area | Bulgaria, BG | Varna | varna | 43 |
| Schengen Area | Poland, PL | Warsaw | warsaw | 10 |
| Schengen Area | Poland, PL | Krakow | krakow | 11 |
| Schengen Area | Poland, PL | Gdansk | gdansk | 12 |
| Schengen Area | Poland, PL | Wroclaw | wroclaw | 13 |
| United Kingdom | United Kingdom, GB | London | london | 47 |
| Canada | Canada, CA | Toronto | toronto | 46 |
| Other Europe / Outside Schengen | Moldova, MD | Chisinau | chisinau | 45 |

The UI groups first by macro region, then localized country, then localized
city. other_centre and not_decided appear after the geographic groups.
Geography must not be confused with slot availability classification.

The survey taxonomy describes centres users may report or select. It is
separate from the runtime provider registry, which describes centres for which
runtime provider configuration exists. Operational provider support requires
its own technical evidence and must not be inferred from survey taxonomy
membership.

No centre may contain static problematic, easy, or has_slots flags. A future
availability observation is a separate versioned record with a value such as
scarce, volatile, relatively_available, or unknown and must include:

- observation_period;
- evidence_source;
- calculated_at in UTC;
- methodology_version.

The idea that Spain, Italy, or sometimes Slovakia may show slots more often is
an analysis hypothesis only. It must not become a centre property or UI hint.

## Legacy centre normalization

| Raw value | Canonical centre_id |
| --- | --- |
| Cologne | cologne |
| Köln | cologne |
| Кёльн | cologne |
| Кельн | cologne |

Store the original values in legacy.centre_values_raw and normalized IDs in
answers.centre_ids. The initial normalization_version is
centre_aliases/1.0.0. Migration statuses are canonical, normalized, unmapped,
and empty.

Never guess an unknown value. Preserve it, mark it unmapped, and route it for
manual taxonomy review. Later normalization appends migration provenance and
does not overwrite the originally ingested value.

## Acceptance criteria for Copilot implementation

- All visible strings exist in uk, ru, and en with English fallback.
- Every question maps exactly once to the data contract.
- Stored values are stable ASCII IDs, not labels.
- Multi-centre, Other, undecided, exclusivity, and conditional clearing rules
  work with keyboard and assistive technology.
- Locale switching and back navigation preserve state.
- The form collects no contact, fingerprint, IP, exact location, User-Agent,
  passport, appointment, or social-listening data.
- Copy states that submission does not subscribe, book, guarantee slots, or
  alter monitoring.

## Copilot implementation handoff

This specification is the approved product input for a later implementation.
For Copilot, survey/spec/ is read-only. Copilot may write only within the scope
allowed by research/user-surveys/AGENTS.md, primarily survey/web-form/.

Changing a question, question_id, option ID, enum, requiredness rule, contract
field, privacy rule, or analytical meaning requires separate human agreement
and a reviewed specification change. Copilot must not independently:

- add, remove, rename, or regroup centres;
- copy centre, problem, or channel enums into parallel handwritten lists;
- change branching or the meaning of Other and Not decided;
- change the submission envelope or introduce production transport behavior;
- add contact collection, telemetry, fingerprinting, or deployment secrets.

The UI must be generated from canonical taxonomy and question configuration
where this specification assigns a single owner. Localized labels are display
data only.

### Form implementation acceptance checklist

- [ ] Only the AGENTS.md writable area is changed.
- [ ] The semantic main content follows the six-section order.
- [ ] All question IDs and contract paths match this specification exactly.
- [ ] All visible strings have uk, ru, and en entries with English fallback.
- [ ] Centre, problem, and channel choices come from canonical taxonomies.
- [ ] Berlin, Cologne, and Munich appear under Germany without duplicate IDs.
- [ ] Other and Not decided branching, exclusivity, and clearing are tested.
- [ ] A language change preserves answers, section, errors, and response_id.
- [ ] Client validation implements this questionnaire's requiredness and limits;
      production ingestion validation is defined separately.
- [ ] Keyboard, labels, focus, status messages, and errors are accessible.
- [ ] Single-submit orchestration and generic submission-failure messaging are
      tested; production transport behavior is defined separately.
- [ ] No personal data, HTML, secrets, raw social data, or localized values are
      submitted.
- [ ] Submission copy explains that this is research, not a subscription,
      booking, availability guarantee, or monitoring configuration change.
