# SDLC Step (d) — Test
University Portal (LUMS-like)

Date: 2026-02-10

## 1) Scope
This test phase validates the MVP portal end-to-end behaviors that are highest risk and most central to correctness:

- Authentication basics (login required, logout ends session)
- Role-based access control (RBAC) boundaries (403 vs 404 where appropriate)
- Courses browsing (list + detail)
- Registration add/drop logic (capacity → enrolled vs waitlisted)
- Transcripts workflow
  - Student: create request, view own requests, download unofficial transcript PDF
  - Registrar: queue access, approve/issue request, download official transcript PDF after issuance
- Support tickets (create ticket, add message, unauthorized user cannot view)
- Finance invoices
  - Student: sees own invoices
  - Finance staff: staff view renders and can filter by student

## 2) Test Approach
Automated tests were added using Django’s built-in test framework (`django.test.TestCase`) to simulate HTTP requests against views and assert:

- Response status codes and redirects
- Database state transitions (e.g., enrollment status changes, transcript status changes)
- Minimal response content checks for key UI indicators (e.g., enrolled badge, invoice reference)
- File download headers for PDF endpoints (`Content-Disposition` filenames)

Primary file:
- app/portal/tests.py

## 3) Standards-Oriented Checks
Django system checks:

- `python manage.py check` → OK (no issues)
- `python manage.py check --deploy` → expected warnings in dev-mode configuration:
  - `SECURE_HSTS_SECONDS` not set
  - `SECURE_SSL_REDIRECT` not enabled
  - `SECRET_KEY` flagged as insecure (auto-generated / insufficient entropy)
  - `SESSION_COOKIE_SECURE` not set
  - `CSRF_COOKIE_SECURE` not set
  - `DEBUG=True`

These are normal for local development but must be addressed before any production deployment.

## 4) Results
Automated suite:

- `python manage.py test`
  - Tests found: 13
  - Result: PASS

## 5) Key Defect Found & Fixed
During test expansion, registration add/drop logic exposed an issue:

- Symptom: first enrollment could be incorrectly waitlisted when section capacity is exactly 1.
- Root cause: seat-availability check counted the just-created enrolled row.
- Fix: compute seat availability excluding the current student before updating enrollment status.

## 6) Known Gaps / Next Improvements
Not yet covered by automated tests (recommended for SDLC Step (e) Improve):

- Front-end UI rendering/visual regressions (Playwright/Selenium)
- CSRF enforcement and security headers in production settings
- Rate limiting / brute-force protection for login
- Permission granularity for staff roles beyond MVP
- Performance tests for large datasets (courses/enrollments/grades)
- PDF content verification (not just headers)
