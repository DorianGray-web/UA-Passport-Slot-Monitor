# Kortrijk Queue Observation

## Status

Approved

## Goal

Passively observe the Kortrijk electronic queue state without modifying,
advancing, or otherwise affecting the booking process.

## Rationale

The project needs reliable evidence about queue availability and state
transitions before implementing user-facing monitoring.

The observer should minimize:

- requests to the provider;
- browser automation;
- retained runtime data;
- privacy and security risks.

## Scope

This specification covers passive observation of:

- the public queue page;
- the state visible during a completed observation;
- transitions between consecutive observations;
- HTTP-first observation;
- browser fallback when HTTP observation is insufficient;
- local metadata recording;
- notifications for selected states.

## Non-goals

The observer must not perform:

- booking;
- automatic slot reservation;
- CAPTCHA solving or bypassing;
- account creation;
- identity verification;
- payment;
- form submission;
- navigation beyond what is required to determine the observable queue state;
- storage of cookies, authorization data, or personal data.

## Queue states

The observer recognizes the following normalized states:

- `NO_SLOTS`
- `SLOTS_AVAILABLE`
- `CAPTCHA_REQUIRED`
- `BLOCKED`
- `UNKNOWN`
- `ERROR`

### State definitions

#### NO_SLOTS

The provider page was successfully observed and contains confirmed markers
indicating that no appointment slots are currently available.

#### SLOTS_AVAILABLE

The provider page was successfully observed and contains confirmed markers
indicating that one or more appointment slots may be available.

#### CAPTCHA_REQUIRED

The observer encountered a CAPTCHA or an equivalent user-verification step
that prevents passive state determination.

#### BLOCKED

The provider or an intermediary rejected or challenged the observation,
including access denial, rate limiting, or a Cloudflare challenge.

#### UNKNOWN

The observation completed, but the available evidence did not match any
confirmed state classifier.

#### ERROR

The observation could not be completed because of a local runtime,
network, parsing, browser, or persistence failure.

## Observation interval

Successful observation cycles must use a randomized delay of:

- minimum: 7 minutes;
- maximum: 12 minutes.

The delay must be selected independently for each new cycle.

Retries caused by transient failures may use a separate bounded backoff policy,
defined in the implementation plan.

## Observation strategy

### Preferred method

Use direct HTTP observation when the response provides enough evidence to
classify the queue state.

### Browser fallback

Use Playwright only when:

- the HTTP request fails;
- the HTTP response is blocked or challenged;
- the HTTP response does not contain enough evidence for reliable
  classification;
- browser-rendered content is required to determine the state.

Browser fallback must remain passive.

It must not:

- submit forms;
- solve CAPTCHA;
- enter personal data;
- reserve a slot;
- continue into the booking workflow.

## Normal observation record

For every completed observation cycle, store:

- timestamp in UTC;
- observation method;
- response time;
- normalized state;
- HTTP status code when available;
- HTML content hash when HTML is available;
- classifier reason or matched marker;
- error category when applicable.

Do not store:

- cookies;
- authorization headers;
- session tokens;
- browser profile data;
- personal data;
- complete request headers unless explicitly sanitized.

## State transitions

A state transition occurs when the current normalized state differs from the
previous successfully recorded normalized state.

Example:

```text
NO_SLOTS -> SLOTS_AVAILABLE

