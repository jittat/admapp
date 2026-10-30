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
projects via a M2M; it can accept a **file upload**, a **URL**, or **either
(applicant's choice)**; it can be
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
`scripts/import_project_uploaded_documents.py` from a CSV (rows matched by
`document_key`; column list in the script's docstring). Column 11 is
`is_required` (`0`/`1`) or else an OR-group `requirement_key`; the optional
columns 14–16 set `major_numbers`, `is_late_upload_allowed` and `validator`
(files with only the first 14 columns still load). The import is one
transaction and stops on an invalid row: an old `if-…` conditional key,
malformed `major_numbers`, `major_numbers` on a row listing several projects,
an unknown validator key, or an unknown project id.

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
| `specifications` | Char(100) | Short spec line under the file input (e.g. "PDF ≤ 2MB"); on a `'url'` slot it is the prompt over the link input. An `'any'` slot shows it in file mode only — link mode shows `url_hint` instead (see below). |
| `notes` | Char(100, blank) | Internal note; appended to `__str__` when present. |

### Upload rules

| Field | Default | Meaning |
|---|---|---|
| `allowed_extentions` | Char | Comma-separated allowed extensions (matched case-insensitively; see `upload_check`). |
| `size_limit` | `2000000` | Max bytes. Note the check is strict `<` (`size_limit <= size` fails), so a file of exactly the limit is rejected. |
| `file_prefix` | Char (blank) | Optional filename prefix. |
| `document_type` | Char, default `'file'` | `'file'` (upload), `'url'` (submit a link, `url_check` path), or `'any'` (**the applicant picks per submission** — a file-or-link toggle in the upload form). Read via the `is_file_document` / `is_url_document` / `is_any_document` properties. |
| `is_required` | Bool (T) | Applicant must provide it (see requiredness below). |
| `is_detail_required` | Bool (F) | The free-text `detail` field must be filled. |
| `can_have_multiple_files` | Bool (F) | Allow multiple `UploadedDocument`s; if false, a new upload **replaces** the previous one (old file + row deleted), regardless of kind — the applicant is asked to confirm first (see the [upload flow](#applicant-upload-flow)). On an `'any'` slot with this on, the applicant can **mix** files and URLs in the same slot. |

### Workflow / keys

| Field | Type | Meaning |
|---|---|---|
| `is_interview_document` | Bool (F) | "ใช้สำหรับสัมภาษณ์" — interview-stage document. Uploads/deletes of these are **still allowed after the application deadline** (all other slots are locked once `project_round.is_deadline_passed()`). |
| `document_key` | Char (blank) | Optional stable key for identifying a slot across imports/scripts. |
| `requirement_key` | Char (blank) | Groups slots into an **OR requirement** and/or a conditional requirement (see below). |
| `major_numbers` | Char(200, blank) | "เฉพาะสาขา" — comma-separated `Major.number`s of the applicant's project. Blank = every applicant of the project; otherwise the slot is **shown, required, and uploadable** only for applicants whose major selection contains one of them (`is_visible_for`). Numbers are project-relative, so do not use it on common or multi-project slots. |
| `criteria_upload_key` | Char(20, blank) | Key of the criteria upload field this slot was [generated from](#criteria-generated-slots); blank for hand-made slots. |
| `is_late_upload_allowed` | Bool (F) | "อัพโหลดหลังหมดเขตได้" — upload/delete stay open after the application deadline up to and including `admission_project.late_upload_date`; no date set = no late upload. |
| `validator` | Char(30, blank) | "การตรวจสอบเพิ่มเติม" — key of a [custom validator](#custom-validators) run on each submission after the basic checks (e.g. `'tcasfolio'`). Blank = none. Plain text, no choices; an unknown key rejects every upload to the slot. |

### Methods

- `is_file_document` / `is_url_document` / `is_any_document` (properties) —
  `document_type` tests; `is_url_document` used to be a DB column and was
  replaced by `document_type` (migration `appl/0106`).
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
| `original_filename` | Char(200, blank) | Original client filename (cut at 200 chars), set by the upload view; kept in full even when the stored name is shortened. Blank on rows uploaded before the view's `orginal_filename` typo was fixed. |
| `document_url` | URLField (blank) | The URL, for URL submissions. |
| `local_document_url` | URLField (blank) | Optional locally-cached URL (preferred over `document_url` in the staff menu when present). Filled for TCASFolio links by [`fetch_mytcasfolio_pdf.py`](#mirrored-tcasfolio-pdfs). |
| `replaced_uploaded_file` | FileField (blank) | The file a link replaced, set only by [`replace_uploaded_files_with_urls.py`](#replacing-files-with-links-script); the file stays on disk. Not shown anywhere and not used by `is_file()` / `is_url()`. |

**Storage path** (`applicant_document_path`):
```
documents/applicant_<applicant.id>/doc_<project_uploaded_document.id>/<filename>
```
under `settings.MEDIA_ROOT`.

The whole path must fit `uploaded_file`'s `max_length` (the `FileField`
default, 100), so `applicant_document_path` **shortens long file names**: it
keeps the last extension and cuts the rest to `MAX_STORED_FILENAME_LENGTH`
(40) characters. With the ~33-character directory prefix and a short
extension, that leaves room for the 8-character `_xxxxxxx` suffix the storage
adds when the name is already taken. That room matters: Django treats
everything after the *first* dot as the extension, so a name like
`ม.5-1-….pdf` cannot be truncated by the storage itself and used to fail with
`SuspiciousFileOperation`. The upload form's own 100-character file name check
is switched off for the same reason.

**Which kind is this row?** Derived, not stored: `is_file()` is
`bool(uploaded_file)`, `is_url()` is "no file but a `document_url`". The
upload view clears the unused field on save, so the two stay exclusive; old
rows classify correctly too. Templates branch **per row** (`d.is_file`), not
on the slot, so a mixed `'any'` slot renders download links and link buttons
side by side. `OldUploadedDocument` has the same two helpers.

**Helpers:** `is_pdf()` (used to choose PDF embed vs. image preview in the
staff viewer); `encrypted_backup_filename()` →
`<pud_id>/<id%100 zero-padded>/media-<id>.enc` (the S3 encrypted-backup key).

### OldUploadedDocument

`appl/models.py:573`. Same shape as `UploadedDocument`
(`related_name='old_uploaded_document_set'`, no `local_document_url`). Used
once, to recover from a disk crash (the `send_data_loss_emails*.py` scripts
read it); surfaced on the applicant page via `prepare_old_uploaded_documents()`
(which caches `applicant.olduploadeddocument_set` keyed by slot id). Do not
reuse it for new purposes.

---

## Applicant upload flow

Views in `appl/views/upload.py`; URLs in `appl/urls.py`.

- **List/render** — the applicant page (`appl/views/__init__.py`) builds
  `common_uploaded_documents = ProjectUploadedDocument.get_common_documents()`
  plus `admission_project.projectuploadeddocument_set.all()`, then
  `prepare_uploaded_document_forms()` attaches a blank `UploadedDocumentForm`
  and the applicant's existing files to each slot. Rendered by
  `appl/templates/appl/include/document_upload_form.html` (a Bootstrap
  accordion card per slot). An `'any'` slot renders a
  อัพโหลดไฟล์ / ระบุลิงก์ radio pair over a file block and a URL block; the
  handler in `document_upload_js.html` (delegated, since the card is replaced
  wholesale after each upload) swaps the blocks, clears the hidden one, and
  toggles `required` on the file input. The file block shows
  `specifications`; the URL block shows `ProjectUploadedDocument.url_hint`
  instead — the slot validator's entry in `DOCUMENT_URL_HINTS` (e.g.
  tcasfolio: "…กรุณาใช้ลิงก์ที่ได้จากระบบ TCASFolio เท่านั้น"), else
  `DEFAULT_URL_HINT` (ลิงก์ไปยังเอกสาร). Both are `gettext_lazy`, so
  translated.

- **Upload** — `POST appl:upload` (`/appl/upload/<document_id>/`), AJAX.
  `upload()`:
  1. resolves the applicant's active application (falls back to
     `accepted_application`); 404/error if none.
  2. if `project_round.is_deadline_passed()` **and** the slot is not an
     interview document → `HttpResponseForbidden`.
  3. picks the submission kind with `get_upload_kind()` — the slot's
     `document_type`, or for `'any'` slots whichever of `request.FILES`
     /`document_url` the applicant actually filled in (neither → `NO_INPUT`) —
     then validates via `UploadedDocumentForm` + `upload_check` (file: size &
     extension & optional detail) or `url_check`. A required `detail` applies
     to both kinds. Only when these basic checks pass, both then run the
     slot's [custom validator](#custom-validators), if any
     (`custom_validation_check()`); this happens **before** step 4, so a
     rejected submission never deletes the previous one.
  4. if the slot is single-file, the previous file+row will be replaced
     (deleted once the new one is saved, see step 5). This is
     destructive, so the **client** asks first: on a single-document slot that
     already holds an entry the card renders a hidden
     `.upload-replace-confirms` panel and the form carries
     `data-replace-confirm`; the submit handler slides the panel down and stops
     instead of uploading, and only ยืนยันการแทนที่ calls `doUpload()`. It
     applies to every `document_type` (a link replacing a file included), is
     skipped when no file/URL was chosen (the server's own error is more
     useful), and closes again when the applicant picks something else. The
     server itself is unguarded — a POST straight to the endpoint still
     replaces.
  5. saves the `UploadedDocument` (applicant, slot, `rank=0`), logs a
     `LogItem`, and returns JSON `{result:'OK', html:<re-rendered card>}`.
     For a single-file slot the replaced documents are deleted only after
     this save succeeds, so a failed save keeps the existing document.
  - Error codes returned to the JS: `FORM_ERROR`, `SIZE_ERROR`, `EXT_ERROR`,
    `DETAIL_REQUIRE`, `URL_INVALID`, `NO_INPUT`, `DETAIL_ERROR`,
    `FILENAME_ERROR`, `APPLICATION_ERROR` (messages hard-coded in
    `document_upload_js.html`), and `VALIDATION_ERROR` (custom validator
    rejection; the JSON also carries a server-rendered `message_html`, shown
    as-is).

- **Download (applicant)** — `appl:document-download`
  (`/appl/doc/<applicant_id>/<project_uploaded_document_id>/<document_id>/`).
  `get_uploaded_document_or_403` enforces that the doc belongs to that
  applicant *and* that slot *and* the logged-in applicant; then
  `download_uploaded_document_response`.

- **Delete** — `POST appl:document-delete` (`.../delete/`). Same ownership
  check and the same deadline/interview-document guard as upload; deletes the
  row, logs, returns the re-rendered card.

### Custom validators

Per-slot content checks beyond size/extension/detail, switched on by setting
`ProjectUploadedDocument.validator` to a registry key. Package
`appl/document_validators/`:

- `base.py` — `ValidationResult(is_valid, code, context)` with
  `ValidationResult.accept()` / `ValidationResult.reject(code, **context)`.
- `__init__.py` — `DOCUMENT_VALIDATORS = {'tcasfolio': tcasfolio.validate}`
  and `run_document_validator(pud, uploaded_file=None, document_url=None)`.
  Blank key → accept. Unknown key → `reject('misconfigured')`; a validator that
  raises → `reject('verification_error')`; both are logged (fail closed). The
  uploaded file is rewound before and after, so the saved file is complete.
- A validator is `fn(project_uploaded_document, uploaded_file=None,
  document_url=None) -> ValidationResult`, called with exactly one of the two
  (whichever kind the applicant submitted).
- `DOCUMENT_URL_HINTS` (key → `gettext_lazy` string) and `get_url_hint(pud)`
  — optional link-input hint for `'any'` slots (see the upload flow); a key
  without an entry gets `DEFAULT_URL_HINT`.
- `tcasfolio.py` — files: the PDF signature check of
  [pdf-signature-verification.md](pdf-signature-verification.md); urls:
  accepted only when (after stripping) they start with
  `https://student.mytcas.com/view-folio/` or
  `https://folio.mytcas.com/view-folio/`, else `reject('invalid_url')`;
  a missing url gives `reject('no_document')`.

In `appl/views/upload.py`, `upload_check` / `url_check` call
`custom_validation_check()` last and return `(is_valid, result_code,
validation_result)`. On rejection `upload()` responds
`{result: 'VALIDATION_ERROR', message_html}`, rendered by
`render_validation_message()` from
`appl/templates/appl/include/document_validation_errors/<key>.html` (falling back
to `default.html`) with `code`, `context`, and `project_uploaded_document`.
The JS puts `message_html` into the card's `.document-upload-errors`.

**Adding a validator:** write the function (reject with short codes), add it to
`DOCUMENT_VALIDATORS`, add `document_validation_errors/<key>.html` with an
`{% if code == ... %}` branch per code (end with an include of `default.html`
for `misconfigured`/`verification_error`), optionally a link hint in
`DOCUMENT_URL_HINTS` (plus its `.po` entry), then set the key on the slot in the
admin. Editing an applicant-facing message only means editing that template.

### Requiredness & OR groups

`check_project_documents()` (`appl/views/__init__.py`) computes completion:
- Every `is_required` slot with zero uploads → error.
- Slots sharing a non-empty `requirement_key` form an **OR group**: at least
  one must be uploaded. The key is only a group name; the old `if-<project>-<major>`
  conditional keys are gone.
- (Also folds in supplement blocks and per-major additional form fields.)

**Major-specific slots.** Conditional-by-major requirements are expressed with
`major_numbers` instead: callers pass `check_project_documents()` only the
slots visible for the applicant's major selection
(`get_visible_project_uploaded_documents()` →
`ProjectUploadedDocument.filter_visible()`), so a slot for majors the applicant
did not pick is neither shown nor required. The same filter is applied on the
applicant page (`index_with_active_application`, `check_application_documents`)
and on the staff applicant page (`backoffice` `show_applicant`). `upload()` and
`document_delete()` return 403 unless `is_available_for_application()` holds —
a common slot, or a slot linked to the application's project and visible for
its selection (previously any slot id was accepted). If an applicant changes
majors, uploads to now-hidden slots are kept but not shown.

**Status box & "application complete" notice.** On the applicant page the
result is shown in `appl/include/application_document_status.html` inside
`#project_status_div_id`. The upload JS (`refreshDocumentStatus()` after an
upload/delete, and after answering a per-major question) re-renders that box
from `check_application_documents` (`appl:check-project-documents`,
`/appl/status/`), so both views must pass the same context.
`application_complete` is true when `is_application_complete()` holds — a
major is selected, `documents_complete_status['status']`, and
`additional_payment == 0` (so free projects need no payment) — and results are
not shown yet (`is_application_complete_notice_shown()` checks
`accepted_for_interview_result_shown` / `accepted_result_shown`). The notice
(`application_complete_notice.html`, "ใบสมัครของคุณสมบูรณ์แล้ว") is rendered
**outside** the status box, above the supplement blocks in
`active_application.html`, in `#application_complete_notice_div_id` (hidden
with `display: none` when incomplete). The status box only carries the flag as
`data-application-complete="1|0"`; after each refresh,
`updateApplicationCompleteNotice()` in `document_upload_js.html` slides the
notice down or up to match. Display only; nothing is stored. A payment shows up
on the next page load, since only uploads and answers trigger the refresh.

**Deadline.** After `project_round.is_deadline_passed()`, upload/delete is
allowed only when `is_uploadable_after_deadline(project)`:
`is_interview_document`, or `is_late_upload_allowed` with
`today <= project.late_upload_date`. The card template reads the same rule from
attributes set by `prepare_deadline_flags()` (`uploadable_after_deadline`,
`late_upload_until` — the cut-off shown in the card header).

### Criteria-generated slots

`AdmissionCriteria.additional_admission_upload_fields_json` rows become slots
via `criteria/upload_documents.py` → `sync_criteria_upload_documents(project)`
(one transaction, safe to re-run):

- For each live criteria (`is_deleted=False`) of a project with
  `is_additional_admission_upload_allowed`, the covered majors are the
  project's `Major`s whose CUPT code matches a `CurriculumMajor` of the
  criteria (`CurriculumMajor.major` is not populated).
- **One slot per upload field** (keyed by the field's stable `key`, stored in
  `criteria_upload_key`), even when the applicant picks several covered majors.
  Values: title + ` (major titles)` (cut to 200 chars), the field's
  `descriptions` / `is_required` / `is_late_upload_allowed`,
  `major_numbers`, `document_type='any'`, `can_have_multiple_files=True`,
  rank `RANK_BASE + criteria index * 100 + field index`, and the module
  constants `DEFAULT_ALLOWED_EXTENSIONS`, `DEFAULT_SIZE_LIMIT`,
  `DEFAULT_SPECIFICATIONS`. These are **overwritten on every sync** — change a
  constant and re-sync; admin edits to generated slots do not survive.
- A generated slot whose field/criteria is gone (or whose project turned the
  flag off) is **deleted** if it has no uploads (`UploadedDocument` /
  `OldUploadedDocument` cascade on delete), otherwise **unlinked** from the
  project with `major_numbers` cleared; if the field comes back, the unlinked
  slot is re-linked.
- Fields whose criteria covers no project major, and repeated keys, are skipped
  and reported in the summary. Hand-made slots (blank `criteria_upload_key`)
  are never touched.

Run it with `scripts/sync_criteria_upload_documents.py <round_id>` (every
project of the round) or the ซิงค์ช่องอัพโหลดเอกสาร button on the criteria
project index (`backoffice:criteria:sync-upload-documents`, POST; admission
admins and super admins only, since it covers every faculty's criteria).

---

## Staff review flow

`backoffice/views/projects.py` (the applicant detail page,
`show_applicant`). It builds the same
`get_common_documents() + project.projectuploadeddocument_set.all()` list and
attaches `applicant_uploaded_documents` per slot, rendered by
`backoffice/templates/backoffice/projects/include/applicant_uploaded_doc_menu.html`
into a side menu with an inline PDF/image previewer (PhotoSwipe / `<embed>`).

Menu rendering, per slot: a slot with no uploads is still listed, greyed out
as `<title> (ไม่มีเอกสาร)`; each entry carries a count badge, and link entries
(per row, `not is_file`) a ลิงก์ badge so links stand out in mixed `'any'`
slots; files carry no type badge. Files open in the previewer; links open in
a new tab, using `local_document_url` when set (else `document_url`), with the
original `document_url` as the hover tooltip. Covered by
`ApplicantUploadedDocMenuTestCase` in `backoffice/tests.py`, which renders
the include directly.

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

### Mirrored TCASFolio PDFs

TCASFolio link submissions are not stored as files, so staff would open the
live TCASFolio page. `scripts/fetch_mytcasfolio_pdf.py` (run by hand from
`scripts/`) mirrors them: for each `UploadedDocument` whose `document_url`
contains `mytcas.com` and whose `local_document_url` is blank, it logs in to
the TCASFolio admin API, downloads the folio's PDF to
`<base_path>/<random 10-digit prefix>-<folio id>.pdf`, and sets
`local_document_url = <base_url>/<that filename>`. Already-mirrored documents
are skipped, so re-runs only pick up new links.

```
python fetch_mytcasfolio_pdf.py <base_path> <base_url>
python fetch_mytcasfolio_pdf.py --dry-run [--limit N]
python fetch_mytcasfolio_pdf.py --refresh [--report FILE] <base_path> <base_url>
# any of these: add --project ID [--major N [N ...]] to limit the run
```

- **Links fetched:** `.../view-folio/<id>` on `folio.mytcas.com` or
  `student.mytcas.com` (the forms the [tcasfolio validator](#custom-validators)
  accepts), plus older `https://folio.mytcas.com/_/<id>` short links. The
  folio id is the last path segment; anything else is reported as
  `wrong url`.
- **Dry run:** `--dry-run` downloads a random sample of `N` (default 10)
  not-yet-mirrored documents into memory and reports size and whether each
  starts with `%PDF`; nothing is written and no row is updated
  (`<base_path>`/`<base_url>` not needed). Use it to check credentials and the
  API before a real run.
- **Refresh:** `--refresh` also re-downloads already-mirrored documents
  (the file is `<base_path>/<basename of local_document_url>`; a
  `local_document_url` not under `<base_url>` is reported as failed). If
  the bytes differ from the local copy, the old copy is kept as
  `<filename>.<YYYYmmdd-HHMMSS>.bak` and the new PDF replaces it under the
  same name, so `local_document_url` is unchanged; a missing local copy is
  written back ("restored"); a download that is not a PDF leaves the old
  copy alone. This assumes TCASFolio PDFs are byte-stable across fetches
  (not yet verified). The run ends with a report of the updated / new /
  restored / failed documents — applicant, document slot, the applicant's
  active applications to the slot's projects with selected majors, and
  sizes — and `--report FILE` also writes it as a CSV (UTF-8 with BOM).
  Cannot be combined with `--dry-run`.
- **Project / major filter:** `--project ID [--major N [N ...]]` (with any
  mode) limits the run to applicants with an active (not canceled)
  application to that project in any round — and, with `--major`, who
  selected any of those major numbers (`MajorSelection.get_major_numbers()`,
  as in the backoffice major lists; paid or not) — and to documents in the
  project's own slots plus common slots. Slot `major_numbers` restrictions
  are not applied. An unknown project or major number is an error, and the
  run prints the selected applicant / document counts first.
- **Files** (in the current directory): `.mytcas-env` with `TCAS_EMAIL` /
  `TCAS_PASSWORD` (a TCASFolio university account), and `mytcas-token.json`,
  the cached access token (written on login, also in a dry run; delete it to
  force a new login). Needs `python-dotenv`.
- **Serving:** the mirrored files are served by whatever serves `<base_path>`
  at `<base_url>`, not through `download_uploaded_document_response`, so the
  app's staff permission check does not apply; unless that server adds its own
  access control, the random filename prefix is the only guard.

### Replacing files with links (script)

`scripts/replace_uploaded_files_with_urls.py` (run by hand from `scripts/`)
turns applicants' uploaded files into links, from a CSV of updates, for one
project and major. The logic is in `maintenance/document_url_replacement.py`
(tests: `python manage.py test maintenance`).

```
python replace_uploaded_files_with_urls.py --project ID --major N updates.csv [--dry-run]
python replace_uploaded_files_with_urls.py --project ID --major N updates.csv --apply
# also: --slot KEY, --report FILE
```

- **CSV:** `national_id,url` (a `national_id,url` header row is optional).
- **Slot:** the project's own file-or-link (`'any'`) slot shown for major
  `N` (blank `major_numbers`, or `N` listed). There must be exactly one;
  otherwise the run stops before any row and lists the candidates (with
  their keys), and `--slot KEY` picks the slot by `document_key` — the
  project's slot or a common slot with that key, exactly one, looked up as in
  `build_portfolio_zips.py` (`find_project_uploaded_document`). It must also
  be a file-or-link slot for `N`. Slots without a `document_key` (e.g.
  criteria-generated ones) can only be used when they are the single
  candidate. An
  unknown major number is an error too. File-only and link-only slots are
  never changed.
- **Applicants:** looked up by `national_id`; must have an active (not
  canceled) application to the project, in any round, with `N` in its
  `MajorSelection`. Others are refused.
- **Url:** stripped, then must pass `URLValidator`, the `document_url`
  length limit, and the slot's [custom validator](#custom-validators) (for
  TCASFolio slots, the `view-folio` link forms).
- **Per row**, the applicant's documents in the slot:
  - exactly one file document → replaced: `replaced_uploaded_file` gets the
    file's name (the file stays on disk), `uploaded_file` is cleared,
    `document_url` is set, `local_document_url` is cleared, and a `LogItem`
    is written. `original_filename` is kept. Each row is saved in its own
    transaction.
  - one link document → compared with the update's link. Same link →
    `already-done` (so re-runs are safe); another one → `url-mismatch`
    warning, not changed. In slots with the `tcasfolio` validator only the
    id at the end counts (last path segment; host, query, fragment and a
    trailing `/` ignored), so `student.mytcas.com/view-folio/<id>`,
    `folio.mytcas.com/view-folio/<id>` and `folio.mytcas.com/_/<id>` all
    match; links with no path compare whole. Other slots compare the whole
    (stripped) urls.
  - none, or several → error, not changed.
- **Dry run:** the default (`--dry-run` says so explicitly; it cannot be
  combined with `--apply`). Rows that would change are reported as
  `to-replace`. Nothing is written without `--apply`.
- **Output:** the changed (or, in a dry run, to-be-changed) rows, then
  warnings and errors, then counts per status; `already-done` rows are not
  listed, only counted; `--report FILE` also writes a CSV (UTF-8 with BOM) with the old
  file and current url per row, enough to undo changes by hand.
- **Afterwards:** run [`fetch_mytcasfolio_pdf.py`](#mirrored-tcasfolio-pdfs)
  to mirror the new TCASFolio links for staff.
- Undoing is manual: move `replaced_uploaded_file` back to `uploaded_file`
  and clear `document_url`. If the applicant later uploads to the slot again,
  the upload view deletes the row (and its current file), so the
  `replaced_uploaded_file` reference is lost; the file itself stays on disk.

---

## `additional_admission_upload_fields` (per-criteria upload documents)

`AdmissionCriteria` is gaining `additional_admission_upload_fields`: a
per-criteria list of extra documents applicants upload *according to the
criteria*, analogous to its existing `additional_admission_form_fields_json`
(text form fields) but for **file uploads** that must "eventually behave like
`ProjectUploadedDocument`" — file validation, storage, single/multi, the
deadline & interview-document rules, and S3-backed serving described above.

Authoring is in the `criteria` app; at runtime the fields are turned into
ordinary `ProjectUploadedDocument` slots by a sync (see
[Criteria-generated slots](#criteria-generated-slots)).

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
  [criteria.md](criteria.md#the-project-index-page). The same card also
  renders on both report pages (`report_index.html`, `report_major.html`),
  which share the cell template; the per-field หลังหมดเขต column needs
  `project` in the template context, so the major report has to pass its
  row's project (and round) into the include.
- A cross-project report at `report/upload-fields/` listing every criteria
  that defines upload fields, with the fields themselves and an expandable
  full-criteria panel. See
  [criteria.md](criteria.md#the-additional-fields-reports); its twin does the
  same for `additional_admission_form_fields_json`.

Definitions currently carry `title`, `descriptions`, `is_required`, and
`is_late_upload_allowed`. Multiple files / URL links are intended to always be
allowed (not per-field options).

### Runtime (implemented)

The fields are materialized as ordinary `ProjectUploadedDocument` slots by the
sync described in [Criteria-generated slots](#criteria-generated-slots), so the
applicant upload flow, storage, staff review/download, and completion checks
are the regular ones above, limited per applicant by `major_numbers` and with
the late-upload rule enforced against `late_upload_date`.

### Not yet done (later phases)

- **Export** — including these fields in the CUPT export pipeline (a separate
  mechanism will be used; see [criteria.md](criteria.md)).
