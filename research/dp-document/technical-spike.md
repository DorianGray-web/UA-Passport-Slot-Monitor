# Technical Feasibility Spike

## Scope

- One provider
- One location
- One service
- No automatic booking
- No production notifications
- No multi-user support

## Questions

- Can availability be detected reliably?
- Is the result available in HTML, XHR, or API response?
- When is CAPTCHA triggered?
- Can a manually verified session be reused?
- How long does the session remain valid?
- What is the safest reasonable check interval?
- Which data must be persisted between checks?

## Success criteria

- Obtain the same availability state twice reliably.
- Detect an intentional or observed state change.
- Store no personal data.
- Stop safely when CAPTCHA appears.
- Document all failed assumptions.
