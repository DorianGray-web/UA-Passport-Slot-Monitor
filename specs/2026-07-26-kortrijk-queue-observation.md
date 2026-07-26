# Kortrijk Queue Observation

## Goal

Observe the queue state without affecting the booking process.

---

## Scope

This specification covers only passive observation.

Out of scope:

- booking
- CAPTCHA solving
- account creation
- payment
- user interaction

---

## States

- NO_SLOTS
- SLOTS_AVAILABLE
- CAPTCHA_REQUIRED
- BLOCKED
- UNKNOWN
- ERROR

---

## Observation interval

Randomized:

7–12 minutes

---

## Normal observation

Store:

- timestamp
- response time
- state
- HTML hash

Do not store:

- cookies
- authorization
- personal data

---

## State change

When state changes:

save

- HTML
- Screenshot
- Extracted text
- Network summary

---

## Notifications

Immediately notify on:

- SLOTS_AVAILABLE
- CAPTCHA_REQUIRED
- UNKNOWN

---

## Browser policy

Preferred:

HTTP observation

Fallback:

Playwright

only after

- HTTP failure
- Cloudflare challenge

---

## Success criteria

The observer can detect every queue state transition while minimizing unnecessary data collection.
