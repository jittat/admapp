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

## Working agreement

For feature work, **describe the plan first and wait for an explicit
go-ahead before editing any files** — even when the request looks small or
fully specified. Answer scoping questions, lay out the files to touch and
the decision points, list open questions, then stop. (Trivial fixes the
user asked for directly are fine to just do.)

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
- `docs/applicant-info.md` — staff-facing applicant show page
  (`backoffice.views.show` + `backoffice/templates/backoffice/show.html`):
  URLs, view flow & access control, `ApplicantForm`, the include-partial
  template structure, and extension points for adding features.
- `docs/admission-project-models.md` — field reference for the core
  `appl/models.py` models: `AdmissionProject` (content + feature flags),
  `AdmissionRound`, `AdmissionProjectRound` (per project+round workflow
  state), and `Major` (slots, fees, CUPT codes). Grouped by purpose with
  what each flag actually controls.
- `docs/uploaded-documents.md` — applicant document uploads: the
  definition→instance model pair (`ProjectUploadedDocument` /
  `UploadedDocument`), applicant upload flow, staff review flow, file
  serving/storage + encrypted S3 backup, major-specific (`major_numbers`) and
  late-upload slots, custom validators, and the per-criteria
  `additional_admission_upload_fields` → slots sync
  (`criteria/upload_documents.py`).
- `docs/criteria.md` — the `criteria` app: data model
  (`AdmissionCriteria`, `ScoreCriteria`, `CurriculumMajor(AdmissionCriteria)`,
  `MajorCuptCode`), the **copy-on-write versioning** of criteria in
  `upsert_admission_criteria`, in-place AJAX toggles, the criteria form UI
  and views/URLs (authoring side only).
- `docs/pdf-signature-verification.md` — TCASFolio PDF signature
  verification (per-slot, not all uploads): what the signed PDFs look like,
  the certificate chain, how the Thailand NRCA root was authenticated, and
  the current decisions (bundle roots, pin the ทปอ. signer, no revocation
  check yet).
- `docs/criteria-export.md` — the CUPT/ทปอ. export pipeline
  (`criteria/views/cuptexport.py`, `cuptexport_fields.py`, `export/*` URLs):
  the two CSVs and how their rows are built, the export config JSON
  (`CuptExportConfig` / custom projects / project rules), custom-project
  re-mapping, portfolio handling, slot adjustment, the validation page,
  CSV/config import, and the field-list constants.
- `docs/major-cupt-code.md` — how `Major` links to `MajorCuptCode` via the
  `cupt_full_code` string, a usage survey of `cupt_full_code` /
  `get_full_major_cupt_code()` (divergent parsers, `detail_items_csv[-2:]`
  bypasses, legacy fallback), and a suggested unification plan.
- `docs/i18n-status.md` — state of the English version (Thai is the
  source language; `en` catalog only): how i18n is wired (`i18n_patterns`
  `/en/` prefix, TH/EN switcher, `title_trans` + `title_en` fields for DB
  titles), the phased implementation plan and its status, and why English
  barely worked — hardcoded Thai in
  applicant templates, a catalog unmaintained since 2018 (fuzzy/untranslated
  entries, no `compilemessages` step, `*.mo` gitignored), missing
  `title_trans` on live pages, relative `LOCALE_PATHS`, and `<html lang>`
  hardcoded to `en`. Client-side translation was considered and rejected.
