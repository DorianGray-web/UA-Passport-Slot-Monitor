# UA Passport Slot Monitor — Project Concept

## 1. Overview

UA Passport Slot Monitor is a web-based service that monitors
appointment availability at Ukrainian document service centers abroad
and notifies users when appointment slots become available.

The project is intended primarily for Ukrainians living in:

- European Union countries;
- the United Kingdom;
- Canada;
- other countries where Ukrainian document centers operate.

The system does not automatically book appointments and does not solve
CAPTCHA challenges. Final registration is always completed manually by
the user.

📢 **We need your feedback!**

This project is currently in its early design and validation stage.

Please take 2 minutes to complete our **[User Survey (Google Forms)](https://forms.gle/yXTAV1aAEh8Z84zN6)** and help us prioritize the features that matter most to future users.

We also welcome feedback from developers, security specialists, UX designers, and open-source contributors. Your ideas, suggestions, and technical reviews can help shape the project before the MVP is implemented.

Feel free to open a GitHub Issue to share your thoughts.

## 2. Problem

Ukrainians living abroad may need to renew or obtain:

- an international passport;
- an ID card;
- documents for a child;
- other available document services.

Appointment slots may remain unavailable for weeks or months.
When new slots appear, they may be claimed within a short period.

Users currently have to repeatedly open the registration website,
select a center and service, pass occasional CAPTCHA challenges, and
check whether appointments are available.

A typical response is:

> No available appointments. Please try again later.

After weeks of unsuccessful checks, the response may suddenly change to:

> 6 available appointments. Confirm registration.

This makes manual monitoring inefficient and unreliable.

## 3. Origin of the project

The project originated from a real personal use case.

The author needed to renew a child's international passport before its
expiration date. For approximately two months, the nearest document
center repeatedly reported that no appointments were available.

A free appointment was eventually discovered by chance. Only six slots
were available, and the offered appointment date was shortly before the
passport expiration date.

This demonstrated that the same problem could affect many Ukrainians
living abroad.

## 4. Proposed solution

The service allows a user to:

1. Share temporary browser geolocation or enter a postal code.
2. Find nearby Ukrainian document service centers.
3. Select one or more centers.
4. Select a document service.
5. Specify the number of applicants.
6. Optionally define a preferred or critical appointment date.
7. Enable monitoring.
8. Receive an immediate notification when availability changes.

## 5. Location discovery

The web application supports:

- temporary browser geolocation;
- postal code input;
- city input;
- manual country and center selection.

Location data is used only to calculate nearby centers.

Whenever possible, the exact location should not be stored after the
user selects the centers to monitor.

## 6. Queue states

The monitoring engine distinguishes between:

- `NO_SLOTS`
- `SLOTS_AVAILABLE`
- `CAPTCHA_REQUIRED`
- `SESSION_EXPIRED`
- `RATE_LIMITED`
- `MAINTENANCE`
- `QUEUE_CLOSED`
- `UNKNOWN_RESPONSE`

An unknown or incomplete response must never be interpreted as
confirmation that no appointments are available.

## 7. CAPTCHA handling

Some registration systems periodically display graphical CAPTCHA
challenges.

The project does not automatically recognize or solve CAPTCHA images.

When a CAPTCHA is detected:

1. Monitoring is paused.
2. The user receives a notification.
3. The user opens the browser session.
4. The CAPTCHA is completed manually.
5. Monitoring resumes using the existing session.

## 8. Notifications

The initial notification channels are:

1. Telegram;
2. email.

Possible later integrations:

- WhatsApp;
- Web Push;
- Signal;
- Discord.

Notifications should include:

- center;
- service;
- number of available appointments, when known;
- offered appointment date, when known;
- detection time;
- direct registration link.

## 9. Platform strategy

The initial client will be a responsive web application or PWA.

This provides access from:

- Android;
- iOS;
- Windows;
- macOS;
- Linux.

Separate native Android and iOS applications are not required for the
initial version.

## 10. Responsible use

The project:

- does not automatically reserve appointments;
- does not bypass CAPTCHA or Cloudflare protection;
- does not collect passport numbers;
- does not sell appointment slots;
- does not create artificial priority;
- respects rate limits;
- pauses after blocking or throttling responses;
- minimizes requests by grouping identical subscriptions.

## 11. Initial MVP

The first version will support:

- one document center;
- one document service;
- availability state detection;
- persistent browser session;
- manual CAPTCHA handling;
- Telegram notifications;
- local event history.

The first implementation will be used to validate the technical
approach before support for additional countries and centers is added.

## 12. Long-term vision

The long-term goal is to create a modular platform for monitoring
Ukrainian document and consular service availability abroad.

Potential providers include:

- passport service centers;
- Ukrainian consulates;
- document issuance services;
- other public appointment systems.

Each external system should be implemented as a separate provider
module without requiring major changes to the monitoring core.
