# Software Requirements Specification (SRS)
## University Portal (LUMS-like) – Responsive Web

**Document ID:** SRS-UP-001  
**Version:** 1.0 (Finalized Requirements)  
**Date:** 2026-02-05  
**Prepared by:** Autonomous SDLC Agent (GitHub Copilot, GPT-5.2)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the requirements for a University Portal application modeled after common capabilities of a university self-service portal (reference: http://portal.lums.edu.pk). The SRS is intended for stakeholders including product owner, university administration, software engineers, QA engineers, security team, and operations.

### 1.2 Scope
The system (“University Portal”) provides role-based access to academic and administrative self-service functions for students, faculty, staff, administrators, and alumni. The portal shall be accessible on desktop and mobile browsers and shall be mobile-enabled by providing a responsive website that runs on Android and iOS browsers.

In scope (high level):
- Authentication and role-based authorization
- Student self-service: registration, timetable, grades, transcript requests, attendance view (if applicable)
- Faculty self-service: class rosters, grade submission, announcements
- Staff self-service: administrative workflows (configurable by office)
- Notifications and announcements
- Profile and settings
- Help/support and issue reporting
- Integrations: SIS (mandatory), Finance (fee status), LMS (SSO/deep links and data exchange where available)

Out of scope (unless added later):
- Full Learning Management System (LMS) content delivery and assignment hosting (portal may provide links and limited integration)
- Payroll/HRMS beyond basic staff profile
- Admissions workflow end-to-end (optional)

### 1.3 Definitions, Acronyms, and Abbreviations
- **SRS**: Software Requirements Specification
- **RBAC**: Role-Based Access Control
- **MFA**: Multi-Factor Authentication
- **PII**: Personally Identifiable Information
- **SIS**: Student Information System (source of record)
- **SSO**: Single Sign-On
- **FERPA-like**: Generic term for education privacy rules (actual compliance depends on jurisdiction)

### 1.4 References
- IEEE 830-1998 (recommended structure for SRS documents)
- Reference portal (availability/content not guaranteed during drafting): http://portal.lums.edu.pk

### 1.5 Overview
Section 2 describes the product context and user classes. Section 3 lists specific functional and nonfunctional requirements, including interfaces, constraints, and quality attributes.

---

## 2. Overall Description

### 2.1 Product Perspective
The University Portal is a new web application that may integrate with existing university systems (e.g., SIS, LMS, finance) through APIs. It is intended as a unified front door for academic and administrative self-service.

### 2.2 Product Functions (Summary)
- Account login via SSO; optional MFA
- View and update user profile (limited fields)
- View announcements and notifications
- Students: course registration/add-drop, timetable, grades, unofficial transcript download, official transcript request/approval, fee invoice/challan view, holds status
- Faculty: course roster, grading submission, class announcements
- Staff/Admin: manage announcements, view reports, manage selected workflows
- Search directory (optional): faculty/staff directory with privacy controls
- Support: FAQs and ticket submission

### 2.3 User Classes and Characteristics
- **Student**: views academic record, registers courses, sees fees/holds
- **Faculty**: manages teaching activities (roster, grading)
- **Staff (Academic Office)**: supports enrollment, scheduling, announcements
- **Finance Staff**: manages fee-related status and statements (if integrated)
- **IT/Admin**: manages roles, permissions, system configuration
- **Alumni**: limited access to academic documents and verification requests per policy

### 2.4 Operating Environment
- Web: latest stable versions of Chrome, Safari, Edge, Firefox
- Mobile: Android (Chrome/WebView), iOS (Safari/WebKit)
- Server: Linux-based container hosting (cloud/on-prem)
- Database: relational DB (e.g., PostgreSQL) (implementation choice)

### 2.5 Design and Implementation Constraints
- Must support secure authentication (SSO integration preferred)
- Must enforce least-privilege RBAC
- Must protect PII and academic records
- Must be mobile-enabled (responsive UI only; no native app or PWA is required for MVP)
- Accessibility: WCAG 2.1 AA target (or equivalent)

### 2.6 User Documentation
- Online help center with role-specific guides
- FAQ and troubleshooting for login/MFA
- Admin guide for announcements and configuration

### 2.7 Assumptions and Dependencies
Because the reference portal content could not be extracted automatically during drafting, the following assumptions apply and must be validated:
- University has an identity provider for SSO (e.g., SAML/OIDC)
- SIS exposes APIs or database views to obtain enrollment, grades, timetable, holds, and program data
- Finance system provides fee invoice/statement status via API export
- LMS provides SSO/deep links and optionally roster/enrollment synchronization
- Data definitions (courses, sections, grading scheme) are provided by SIS

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces
- UI-1: The portal shall provide a responsive web UI supporting viewport widths from 320px to 1920px.
- UI-2: The portal shall provide a consistent navigation structure with role-based menus.
- UI-3: The portal shall support dark mode (optional, configurable) without loss of readability.
- UI-4: The portal shall provide touch-friendly controls and layouts on mobile devices (minimum target size and spacing per platform conventions).

#### 3.1.2 Hardware Interfaces
- None required beyond standard client devices (desktop, laptop, tablet, smartphone).

#### 3.1.3 Software Interfaces
- SI-1: The portal shall integrate with an Identity Provider using OIDC or SAML 2.0.
- SI-2: The portal shall integrate with SIS via REST/GraphQL APIs or batch import.
- SI-3: The portal shall integrate with Finance system for fee status via API or batch import.
- SI-4: The portal shall support email notification delivery via SMTP or a transactional email provider.
- SI-5: The portal shall integrate with LMS via SSO and deep links, and may exchange roster/enrollment data where available.

#### 3.1.4 Communications Interfaces
- CI-1: All client-server communication shall occur over HTTPS (TLS 1.2+).
- CI-2: The portal shall support HTTP/2 where available.

### 3.2 Functional Requirements

#### 3.2.1 Authentication and Session
- FR-AUTH-1: The system shall allow users to authenticate using SSO.
- FR-AUTH-2: The system shall support optional MFA enforcement by policy.
- FR-AUTH-3: The system shall automatically log out idle sessions after a configurable timeout.
- FR-AUTH-4: The system shall prevent concurrent session abuse via configurable session controls.

#### 3.2.2 Authorization and Roles
- FR-RBAC-1: The system shall implement RBAC with roles at minimum: Student, Faculty, Staff, Registrar Staff, Finance Staff, IT/Admin, Alumni.
- FR-RBAC-2: The system shall restrict access to academic records to authorized roles only.
- FR-RBAC-3: The system shall provide an admin interface to assign roles and permissions.

#### 3.2.3 Student Services
- FR-STU-1: The system shall allow students to view their current program, term, and academic standing.
- FR-STU-2: The system shall allow students to view course offerings for a selected term.
- FR-STU-3: The system shall allow students to register for courses subject to eligibility rules (prerequisites, capacity, holds).
- FR-STU-4: The system shall support add/drop within configured date windows.
- FR-STU-5: The system shall display a student timetable with conflict detection.
- FR-STU-6: The system shall display grades per term once released.
- FR-STU-7: The system shall provide an **unofficial transcript** view and downloadable PDF to the student.
- FR-STU-8: The system shall provide an **official transcript request** workflow that requires review and approval before issuance.
- FR-STU-9: The system shall allow the student to track official transcript request status (e.g., Submitted, In Review, Approved, Rejected, Issued).
- FR-STU-10: The system shall deliver the official transcript as an approved, tamper-evident PDF (e.g., signed and/or with verification code) according to institutional policy.
- FR-STU-11: The system shall show holds (financial/disciplinary/advising) that affect registration.
- FR-STU-12: The system shall show fee invoice/statement status and due dates (if integrated).

#### 3.2.3.1 Official Transcript Request and Approval
- FR-TRN-1: The system shall allow students and alumni (as permitted) to submit an official transcript request.
- FR-TRN-2: The request form shall capture required metadata (purpose, delivery method, recipient details if applicable, and consent acknowledgement).
- FR-TRN-3: The system shall route requests to authorized Registrar Staff for review.
- FR-TRN-4: Registrar Staff shall be able to approve or reject a request with a reason.
- FR-TRN-5: The system shall enforce policy checks prior to approval (e.g., identity verified, no blocking holds, fees paid where applicable).
- FR-TRN-6: The system shall generate an audit log entry for request submission, review, approval/rejection, and issuance.

#### 3.2.4 Faculty Services
- FR-FAC-1: The system shall list courses taught by a faculty member for a selected term.
- FR-FAC-2: The system shall provide class rosters with student identifiers per policy.
- FR-FAC-3: The system shall allow faculty to submit grades for enrolled students.
- FR-FAC-4: The system shall support draft grading and final submission with audit trail.
- FR-FAC-5: The system shall allow faculty to post course announcements visible to enrolled students.

#### 3.2.5 Announcements and Notifications
- FR-NOTIF-1: The system shall display global announcements and role-targeted announcements.
- FR-NOTIF-2: The system shall allow users to view a notification inbox.
- FR-NOTIF-3: The system shall send email notifications for critical events (e.g., grade release, registration window changes) based on policy.
- FR-NOTIF-4: The system shall send email notifications for workflow events (e.g., official transcript request status changes) based on user role and policy.

#### 3.2.6 Profile and Preferences
- FR-PROF-1: The system shall allow users to view their profile information.
- FR-PROF-2: The system shall allow users to update permitted fields (e.g., phone, address) with validation.
- FR-PROF-3: The system shall allow users to set communication preferences subject to institutional policy.

#### 3.2.7 Support and Feedback
- FR-SUP-1: The system shall provide an FAQ/Help section.
- FR-SUP-2: The system shall allow users to submit a support ticket with category and description.
- FR-SUP-3: The system shall provide ticket status tracking to the submitter.

#### 3.2.8 Administration
- FR-ADM-1: The system shall allow admins to manage announcements (create, edit, schedule, expire).
- FR-ADM-2: The system shall allow admins to configure term calendars (registration windows, grade release windows).
- FR-ADM-3: The system shall provide audit logs for sensitive actions (role changes, grade submission, transcript export).
- FR-ADM-4: The system shall provide basic usage analytics dashboards (logins, feature usage) with privacy safeguards.
- FR-ADM-5: The system shall provide administrative queues for Registrar Staff and Finance Staff to review and process applicable requests.

### 3.3 Performance Requirements
- PR-1: The system shall support at least 5,000 concurrent active users (configurable target).
- PR-2: For 95% of requests, the system shall respond within 2 seconds for read-only pages under nominal load.
- PR-3: Bulk operations (e.g., grade submission upload) shall complete within 30 seconds for typical class sizes (≤300 students).

### 3.4 Logical Database Requirements
- DB-1: The system shall store user roles, permissions, preferences, and audit logs.
- DB-2: The system may cache SIS data but shall identify the system-of-record fields.
- DB-3: Audit logs shall be immutable and retained for a configurable period with a minimum default of 7 years.
- DB-4: The system shall store transcript request records, status transitions, and approvals as part of the audit trail.

### 3.5 Design Constraints
- DC-1: The system shall comply with institutional security policies.
- DC-2: The system shall use encryption at rest for sensitive data where supported.
- DC-3: The system shall implement secure coding practices aligned with OWASP ASVS (Level 2 target).

### 3.6 Software System Attributes (Quality Requirements)

#### 3.6.1 Security
- SEC-1: The system shall enforce HTTPS and secure cookies.
- SEC-2: The system shall implement CSRF protections and input validation.
- SEC-3: The system shall implement rate limiting and account lockout policies via IdP and/or application.
- SEC-4: The system shall log security-relevant events (login failures, privilege changes).
- SEC-5: The system shall be designed and tested to mitigate OWASP Top 10 risks.
- SEC-6: The system shall implement least-privilege access controls and separation of duties for grade submission and official transcript issuance.
- SEC-7: Sensitive documents (e.g., official transcripts) shall be protected against unauthorized access and shall not be publicly guessable via URLs.

#### 3.6.2 Reliability and Availability
- REL-1: The system shall target 99.5% monthly uptime (excluding planned maintenance).
- REL-2: The system shall provide graceful degradation if upstream SIS/Finance systems are unavailable (read-only cached data where allowed, clear error messages).

#### 3.6.3 Maintainability
- MAIN-1: The system shall use modular architecture enabling independent feature development.
- MAIN-2: The system shall provide centralized configuration for term calendars and feature flags.

#### 3.6.4 Portability (Mobile Enablement)
- PORT-1: The system shall run on Android and iOS via mobile browsers.
- PORT-2: The system shall be optimized for mobile network conditions (efficient payloads and caching for static assets).

#### 3.6.5 Usability and Accessibility
- USA-1: The system shall meet WCAG 2.1 AA for key user flows.
- USA-2: The system shall support keyboard navigation and screen readers.

### 3.7 Other Requirements
- OR-1: The system shall provide data export for admins (CSV) subject to authorization.
- OR-2: The system shall display localized date/time formats; multi-language support is optional.

---

## Appendix A: Requirements Decisions (Final)
1. **Mobile enablement:** Responsive website only (no native apps or PWA required for MVP).
2. **MVP integrations:** SIS + Finance + LMS integration as available (at minimum SIS is mandatory).
3. **MVP roles:** Include all roles (Student, Faculty, Staff, Registrar Staff, Finance Staff, IT/Admin, Alumni).
4. **Transcripts:** Unofficial transcripts are available for direct download; official transcripts require request and approval.
5. **Security:** Follow standards (OWASP ASVS L2 target, mitigate OWASP Top 10, strong audit trails and least privilege).

## Appendix B: Assumption Validation Checklist
- Confirm IdP protocol (OIDC vs SAML)
- Confirm SIS integration method and data contract
- Confirm finance data sources and refresh frequency
- Confirm LMS integration method (SSO/deep links and any data exchange)
- Confirm peak concurrency and performance SLAs

---

## Sign-off (Placeholder)
- Product Owner: ____________________ Date: ________
- IT Security: _______________________ Date: ________
- Registrar/Academic Office: _________ Date: ________
