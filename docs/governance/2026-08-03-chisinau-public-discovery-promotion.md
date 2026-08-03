# Chisinau Public-Discovery Capability Decision

**Decision:** Approved

**Decision date:** 2026-08-03

**Decision authority:** Project owner

## Evidence reviewed

- [Chisinau live observation](../../research/dp-document/2026-08-03-chisinau-live-observation.md)
- centre `45`;
- service `4`;
- 25 allowed dates;
- recognized non-empty `TIMES` response;
- bounded `LANDING -> DAYS -> TIMES -> STOP` behavior.

## Capability

The `chisinau-v1` public-discovery profile is approved for HTTP-first bounded
discovery. The existing experimental Playwright transport remains opt-in and
may be used only after HTTP `BLOCKED`. Both transports stop at `TIMES`.

This decision does not authorize identity submission, CAPTCHA interaction,
OTP, reservation, booking, or inference for another deployment.
