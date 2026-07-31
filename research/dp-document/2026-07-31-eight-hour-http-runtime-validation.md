# Eight-Hour HTTP Runtime Validation — 2026-07-31

## Scope

This report records an approximately eight-hour runtime validation of the
current HTTP-first monitoring architecture for:

- Madrid;
- London;
- Milan.

This is runtime-generated project evidence. It is distinct from
owner-provided passive browser observations, repository-derived frontend
analysis, offline tests, and sanitized fixtures.

The session tested the existing landing-stage monitor and did not perform
identity verification, CAPTCHA interaction, booking, or browser automation.

## Runtime stability

All three provider processes ran continuously for approximately eight hours.
The session confirmed that:

- configured startup delays operated correctly;
- append-only Observation recording remained stable;
- cooldown after repeated HTTP `403` responses operated as designed;
- no runtime crash or provider-process failure was observed.

## HTTP blocking behavior

Repeated blocked observations consistently contained:

- HTTP status `403`;
- the same Cloudflare response page hash;
- the stable normalized state `BLOCKED`.

For an unchanged blocked response, the transition was:

```text
BLOCKED -> BLOCKED
```

The transition policy correctly emitted no new diagnostic event. The
resulting diagnostic decision was `NOT_REQUIRED`, with no browser
investigation enqueued.

This confirms that diagnostics are event-driven rather than
observation-driven: classification as `BLOCKED` alone does not request a new
investigation on every polling cycle. A diagnostic event requires a relevant
state transition or other configured change evidence.

## Intermittent public-form observations

During the same session, Madrid and Milan intermittently returned HTTP `200`
instead of HTTP `403`. Their Observations recorded:

- `HTTP_200`;
- `QUEUE_FORM_FOUND`;
- `SERVICE_CENTER_FOUND`;
- `UNRECOGNIZED_HTML`.

This evidence confirms that the HTTP transport reached the public queue form
and detected the service-centre context.

The normalized state was correctly reported as `UNKNOWN` because this HTML
version does not yet have a confirmed provider classifier. In this context,
`UNKNOWN` is not a transport or runtime error. It means:

- the public queue form was detected;
- the service centre was detected;
- the HTTP request succeeded;
- the returned HTML did not match a currently confirmed terminal or
  discovery-ready classifier.

London remained consistently `BLOCKED` in the recorded session; this report
does not claim that its public form was reached by the HTTP monitor.

## Architectural conclusion

The experiment confirms that the current HTTP architecture can reach the
public queue interface. For the observed Madrid and Milan responses, the
limitation is classifier coverage rather than HTTP transport reliability.

The runtime must continue treating unconfirmed successful HTML as `UNKNOWN`.
It must not infer `NO_SLOTS`, available dates, or available times from the
presence of a form alone.

The next research milestone is to extend fixture-backed, confirmed provider
classification beyond `LANDING` to the publicly accessible `DAYS` and
`TIMES` stages:

```text
LANDING -> DAYS -> TIMES -> STOP
```

Identity verification, CAPTCHA interaction, fingerprint generation, and
booking remain outside the monitoring scope.

## What this session does not establish

The session does not establish:

- that the `DAYS` or `TIMES` endpoints were executed by the monitor;
- normalized date or time-slot availability;
- identical HTML, CSRF handling, or response schemas across centres;
- public calendar availability for London during this session;
- any behavior beyond the first identity-verification boundary.

