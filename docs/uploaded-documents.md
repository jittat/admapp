# Uploaded Documents

How applicant document uploads work: the **definition vs. instance** model
pair (`ProjectUploadedDocument` / `UploadedDocument`), the applicant upload
flow, the staff review flow, and how files are stored/served/backed up. This
is a code-reading of `appl/models.py`, `appl/views/upload.py`,
`appl/views/__init__.py`, `backoffice/views/projects.py`, and their
templates — a point-in-time analysis; verify against current code.

It also includes a section at the end on
**`additional_admission_upload_fields`** — the per-criteria upload documents
on `AdmissionCriteria` that are meant to eventually behave like
`ProjectUploadedDocument` (contrast with the JSON-blob
`additional_admission_form_fields_json` — see [criteria.md](criteria.md)) —
covering what is implemented so far and what is left.

## The two-model pattern

Document uploads use a **definition → instance** split (like a form field
vs. a submitted value):

- **`ProjectUploadedDocument`** — the *definition* of a document slot a
  project requires ("transcript", "portfolio", "ID card"). Staff-defined,
  attached to projects, ordered by `rank`. One per required document type.
- **`UploadedDocument`** — the *instance*: an actual file (or URL) an
  applicant submitted against a slot. FK to both `Applicant` and
  `ProjectUploadedDocument`.

A slot can be **common** (shown for every project) or attached to specific
projects via a M2M; it can accept a **file upload** or a **URL**; it can be
**single** or **multi-file**. Requiredness and grouped "one of these"
requirements are expressed on the definition.

```
ProjectUploadedDocument (slot/definition)   1 ──< UploadedDocument (applicant's file)
   ├─ admission_projects  (M2M)                     ├─ applicant (FK)
   └─ is_common_document → shown on all projects     └─ project_uploaded_document (FK, related_name=uploaded_document_set)
```

---

## ProjectUploadedDocument

`appl/models.py:484`. The staff-defined document slot. `Meta.ordering =
['rank']`. Registered in the Django admin (`appl/admin.py`), and also editable
as a `StackedInline` on `AdmissionProject` (through the M2M). Bulk-loaded by
`scripts/import_project_uploaded_documents.py`.

### Attachment & ordering

| Field | Type | Meaning |
|---|---|---|
| `admission_projects` | M2M `AdmissionProject` (blank) | Which projects show this slot. |
| `is_common_document` | Bool (F) | "ใช้ทุกโครงการ" — shown on **every** project regardless of the M2M. Fetched by the static `get_common_documents()`. |
| `rank` | Int | Display order. |

### Content / instructions

| Field | Type | Meaning |
|---|---|---|
| `title` | Char | Slot name shown to applicant/staff. |
| `descriptions` | Text | Longer instructions (rendered with linebreaks). |
| `specifications` | Char(100) | Short spec line under the file input (e.g. "PDF ≤ 2MB"). |
| `notes` | Char(100, blank) | Internal note; appended to `__str__` when present. |

### Upload rules

| Field | Default | Meaning |
|---|---|---|
| `allowed_extentions` | Char | Comma-separated allowed extensions (matched case-insensitively; see `upload_check`). |
| `size_limit` | `2000000` | Max bytes. Note the check is strict `<` (`size_limit <= size` fails), so a file of exactly the limit is rejected. |
| `file_prefix` | Char (blank) | Optional filename prefix. |
| `is_url_document` | Bool (F) | If true, the applicant submits a **URL** instead of a file (`url_check` path). |
| `is_required` | Bool (T) | Applicant must provide it (see requiredness below). |
| `is_detail_required` | Bool (F) | The free-text `detail` field must be filled. |
| `can_have_multiple_files` | Bool (F) | Allow multiple `UploadedDocument`s; if false, a new upload **replaces** the previous one (old file + row deleted). |

### Workflow / keys

| Field | Type | Meaning |
|---|---|---|
| `is_interview_document` | Bool (F) | "ใช้สำหรับสัมภาษณ์" — interview-stage document. Uploads/deletes of these are **still allowed after the application deadline** (all other slots are locked once `project_round.is_deadline_passed()`). |
| `document_key` | Char (blank) | Optional stable key for identifying a slot across imports/scripts. |
| `requirement_key` | Char (blank) | Groups slots into an **OR requirement** and/or a conditional requirement (see below). |

### Methods

- `get_common_documents()` (static) — all `is_common_document=True` slots.
- `get_uploaded_documents_for_applicant(applicant)` — this slot's
  `UploadedDocument`s for one applicant (via `related_name='uploaded_document_set'`).

---

## UploadedDocument

`appl/models.py:542`. One applicant's submission against a slot.

| Field | Type | Meaning |
|---|---|---|
| `applicant` | FK `Applicant` | Owner. |
| `project_uploaded_document` | FK (`related_name='uploaded_document_set'`) | The slot. |
| `rank` | Int | Ordering among multiple files (set to `0` on upload). |
| `detail` | Char(200, blank) | Free-text label/description (required when the slot's `is_detail_required`). |
| `uploaded_file` | FileField | The file; `upload_to=applicant_document_path`. Blank for URL documents. |
| `original_filename` | Char(200, blank) | Original client filename. (Note: the upload view assigns `orginal_filename` — a **typo attribute**, not this field; `original_filename` is largely unset via the normal flow.) |
| `document_url` | URLField (blank) | The URL, for `is_url_document` slots. |
| `local_document_url` | URLField (blank) | Optional locally-cached URL (preferred over `document_url` in the staff menu when present). |

**Storage path** (`applicant_document_path`):
```
documents/applicant_<applicant.id>/doc_<project_uploaded_document.id>/<filename>
```
under `settings.MEDIA_ROOT`.

**Helpers:** `is_pdf()` (used to choose PDF embed vs. image preview in the
staff viewer); `encrypted_backup_filename()` →
`<pud_id>/<id%100 zero-padded>/media-<id>.enc` (the S3 encrypted-backup key).

### OldUploadedDocument

`appl/models.py:573`. Same shape as `UploadedDocument`
(`related_name='old_uploaded_document_set'`, no `local_document_url`). Holds
prior-round/archived uploads so they can be shown read-only; surfaced on the
applicant page via `prepare_old_uploaded_documents()` (which caches
`applicant.olduploadeddocument_set` keyed by slot id).

---

## Applicant upload flow

Views in `appl/views/upload.py`; URLs in `appl/urls.py`.

- **List/render** — the applicant page (`appl/views/__init__.py`) builds
  `common_uploaded_documents = ProjectUploadedDocument.get_common_documents()`
  plus `admission_project.projectuploadeddocument_set.all()`, then
  `prepare_uploaded_document_forms()` attaches a blank `UploadedDocumentForm`
  and the applicant's existing files to each slot. Rendered by
  `appl/templates/appl/include/document_upload_form.html` (a Bootstrap
  accordion card per slot).

- **Upload** — `POST appl:upload` (`/appl/upload/<document_id>/`), AJAX.
  `upload()`:
  1. resolves the applicant's active application (falls back to
     `accepted_application`); 404/error if none.
  2. if `project_round.is_deadline_passed()` **and** the slot is not an
     interview document → `HttpResponseForbidden`.
  3. validates via `UploadedDocumentForm` + `upload_check` (file: size &
     extension & optional detail) or `url_check` (URL slots).
  4. if the slot is single-file, deletes the previous file+row first.
  5. saves the `UploadedDocument` (applicant, slot, `rank=0`), logs a
     `LogItem`, and returns JSON `{result:'OK', html:<re-rendered card>}`.
  - Error codes returned to the JS: `FORM_ERROR`, `SIZE_ERROR`, `EXT_ERROR`,
    `DETAIL_REQUIRE`, `URL_INVALID`, `DETAIL_ERROR`, `FILENAME_ERROR`,
    `APPLICATION_ERROR`.

- **Download (applicant)** — `appl:document-download`
  (`/appl/doc/<applicant_id>/<project_uploaded_document_id>/<document_id>/`).
  `get_uploaded_document_or_403` enforces that the doc belongs to that
  applicant *and* that slot *and* the logged-in applicant; then
  `download_uploaded_document_response`.

- **Delete** — `POST appl:document-delete` (`.../delete/`). Same ownership
  check and the same deadline/interview-document guard as upload; deletes the
  row, logs, returns the re-rendered card.

### Requiredness & OR groups

`check_project_documents()` (`appl/views/__init__.py`) computes completion:
- Every `is_required` slot with zero uploads → error.
- Slots sharing a non-empty `requirement_key` form an **OR group**: at least
  one must be uploaded. If the key starts with `if`, the group is only
  required when `check_project_document_condition()` matches the applicant's
  major selection (conditional-by-major requirement).
- (Also folds in supplement blocks and per-major additional form fields.)

---

## Staff review flow

`backoffice/views/projects.py` (the applicant detail page,
`show_applicant`). It builds the same
`get_common_documents() + project.projectuploadeddocument_set.all()` list and
attaches `applicant_uploaded_documents` per slot, rendered by
`backoffice/templates/backoffice/projects/include/applicant_uploaded_doc_menu.html`
into a side menu with an inline PDF/image previewer (PhotoSwipe / `<embed>`).

- **Staff download** — `backoffice:projects-download-app-document`
  (`.../doc/<pud_id>/<uploaded_doc_id>/`). `download_applicant_document`
  reuses `download_uploaded_document_response` after
  `load_applicant_application_and_check_permission` (staff can only view
  applicants in projects/majors they're allowed to).
- **Check marks** — the staff "reviewed/verified" state is **not** on the
  document models; it lives in `CheckMarkGroup` (backoffice), toggled via
  `check_mark_toggle`. Documents themselves have no approve/reject field.

---

## File serving, storage & backup

`download_uploaded_document_response` (`appl/views/upload.py`):
- Reads the file from `MEDIA_ROOT`, sniffs the MIME type with `python-magic`
  (`get_file_mime_type`, which retries a few filename encodings for legacy
  TIS-620 paths), and streams it with the detected `Content-Type`.
- **Fallback to encrypted S3 backup**: if the local file is missing (MIME
  `None`), it fetches `encrypted_backup_filename()` from the S3 backup bucket
  and **decrypts** it with Fernet (`settings.S3_MEDIA_BACKUP_*` /
  `S3_MEDIA_BACKUP_ENCRYPTION_KEY`) before serving. Backup population is done
  by `scripts/backup_*` (e.g. `backup_uploaded_documents_to_s3.py`).

Both applicant and staff download paths funnel through this one function, so
they share MIME handling and the S3 fallback.

---

## `additional_admission_upload_fields` (per-criteria upload documents)

`AdmissionCriteria` is gaining `additional_admission_upload_fields`: a
per-criteria list of extra documents applicants upload *according to the
criteria*, analogous to its existing `additional_admission_form_fields_json`
(text form fields) but for **file uploads** that must "eventually behave like
`ProjectUploadedDocument`" — file validation, storage, single/multi, the
deadline & interview-document rules, and S3-backed serving described above.

This is being built in phases. Only the **authoring** side is implemented so
far; the runtime (applicant upload, staff review) is not yet wired up.

### Implemented (authoring, in the `criteria` app)

- `AdmissionProject.is_additional_admission_upload_allowed` — the per-project
  opt-in flag that gates the whole feature.
- `AdmissionCriteria.additional_admission_upload_fields_json` — the field
  *definitions*, stored as a JSON blob (like
  `additional_admission_form_fields_json`), read via
  `get_additional_admission_upload_fields()` which returns entries of
  `{title, descriptions, is_required, is_late_upload_allowed}`.
- `AdmissionProject.is_additional_admission_late_upload_allowed` — a second,
  nested opt-in that adds the per-field `is_late_upload_allowed` checkbox
  ("อัพโหลดหลังหมดเขต"). It only means anything when the upload flag above is
  also on; with it off, extraction forces every row's value to `False`.
  `AdmissionProject.late_upload_date` ("วันสุดท้ายที่อนุญาตให้อัพโหลดล่าช้าได้")
  is the cut-off; it reaches the criteria editor's help text through
  `additional_fields_context` and is displayed when set, but nothing enforces
  it yet — that is for the runtime phases below.
- Editing UI in the criteria create/edit form
  (`criteria/include/additional_upload_fields.html`), extracted from POST and
  carried through the criteria **copy-on-write versioning** in
  `upsert_admission_criteria` (see [criteria.md](criteria.md)).
- A read-only display on the criteria index page
  (`criteria/include/scorecriteria_col_additional_info.html`) — a collapsed
  อัพโหลดเพิ่มเติม note that expands to the defined rows, for staff checking
  criteria by hand. It shows stored definitions even when
  `is_additional_admission_upload_allowed` has since been turned off. See
  [criteria.md](criteria.md#the-project-index-page).

Definitions currently carry `title`, `descriptions`, `is_required`, and
`is_late_upload_allowed`. Multiple files / URL links are intended to always be
allowed (not per-field options).

### Not yet done (later phases)

- **Materialization** — turning the per-criteria definitions into concrete
  per-major upload *slots*.
- **Applicant upload flow** — letting applicants actually upload files/URLs
  against these fields, with the same storage, deadline/interview-document
  rules, and multi-file handling as `UploadedDocument`.
- **Staff review** — surfacing these uploads on the applicant detail page /
  download paths.
- **Completion checks** — whether required upload fields participate in
  application-completeness validation.
- **Export** — including these fields in the CUPT export pipeline (a separate
  mechanism will be used; see [criteria.md](criteria.md)).
