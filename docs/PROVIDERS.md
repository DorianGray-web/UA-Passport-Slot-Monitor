# Providers

Provider support is implemented through adapters. Each adapter translates one public appointment system into the project's normalized availability states.

Listing a provider in this document does not mean that production support is available.

## Provider acceptance principles

Before an adapter is added, the project should confirm that:

- the relevant appointment workflow is publicly available;
- monitoring can be performed without bypassing access controls;
- challenge and error states can be distinguished from valid availability responses;
- a responsible polling strategy can be defined;
- the adapter does not require passport numbers or document details;
- final registration remains on the official provider website.

## DP Document

**Research status:** Active feasibility study

**First research location:** Kortrijk, Belgium

The initial study has confirmed that the public client application exposes the general appointment sequence:

1. service selection;
2. available-day lookup;
3. available-time lookup;
4. manual registration.

Direct HTTP access may be rejected while the public appointment application remains accessible through a normal browser session. This makes browser-assisted research and reliable capture validation relevant to the adapter design.

The following items are not yet confirmed or implemented:

- stable capture of live availability data;
- normalized day and time-slot responses;
- persistent session requirements;
- safe polling limits;
- a production Kortrijk adapter;
- support for other DP Document locations.

## Public documentation boundary

Provider documentation describes observable workflow stages, supported states, limitations, and safety decisions. It must not include secrets, session data, CAPTCHA tokens, browser profiles, fingerprints, raw network captures, or detailed reproduction recipes for internal provider requests.
