# admapp

Django-based admission management system (Kasetsart University admission
projects: applications, criteria-based scoring, interview calls,
acceptance, document uploads, etc.). UI/labels are primarily Thai.

## Apps

- **`regis`** — applicant accounts/registration (`Applicant`, `LogItem`,
  auth-related models).
- **`appl`** — core admission domain model: `AdmissionProject`,
  `AdmissionRound`, `AdmissionProjectRound` (per project+round settings),
  `Major`, `ProjectApplication`, `AdmissionResult` (per-applicant/major
  scoring & decisions), payments, exam scores.
- **`backoffice`** — staff-facing views/templates for reviewing
  applicants, scoring, interview-call decisions, acceptance, document
  review, comments/check-marks. Most admin workflows live in
  `backoffice/views/projects.py`.
- **`criteria`** — selection criteria definitions/evaluation used to
  compute `calculated_score` / `is_criteria_passed` on `AdmissionResult`.
- **`supplements`** — supplementary forms/data collected from applicants
  for specific projects.
- **`qrconfirmations`** — QR-code based confirmation flows.
- **`api`** — REST API (DRF).
- **`main`** — public-facing site.
- **`backupmedia`** — media backup utility/scripts.

## Where to look

- Staff score/interview-call UI:
  `backoffice/views/projects.py` (`show_scores`, `show_applicant`,
  `update_interview_call_score`, `set_call_for_interview`,
  `update_individual_interview_call_score`) +
  `backoffice/templates/backoffice/projects/`.
- Core data model: `appl/models.py` (`AdmissionProjectRound`, `Major`,
  `AdmissionResult`, `MajorInterviewCallDecision` is in
  `backoffice/models.py`).
- Setup/install instructions: `README.md`.

## Docs

Deeper, module-specific analysis docs are kept in `docs/*` as they're
written (not auto-derived — read them for context before working on that
area, but verify against current code since they're point-in-time
analyses):

- `docs/interview-call.md` — interview-call decision model (bulk
  score-cutoff vs. per-applicant decisions), score-list page, per-applicant
  page, and the AJAX endpoints that update `AdmissionResult.is_accepted_for_interview`.
