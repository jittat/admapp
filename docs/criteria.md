# Criteria Module

This document describes the `criteria` app: how admission criteria are
modeled, how they are edited with **copy-on-write versioning**, and how
curriculum majors are linked. It is the result of a code-reading session
over the app (`criteria/models/`, `criteria/views/__init__.py`,
`criteria/urls.py`, `criteria_options.py`, templates). It is a
point-in-time analysis — verify against current code.

The **CUPT/ทปอ. export/import pipeline** (`criteria/views/cuptexport.py`,
`cuptexport_fields.py` and the `export/*` URLs) lives in its own document:
[criteria-export.md](criteria-export.md).

## What the app is (and isn't)

The `criteria` app is where staff **define and publish** the admission
criteria for each project+faculty: the required conditions (min scores /
qualifications), the scoring weights, which curriculum majors a criteria
applies to, slot counts, interview dates, accepted student types, etc. It
also owns the **CUPT export/import** pipeline that turns those definitions
into the CSV files uploaded to the central admission system — documented
separately in [criteria-export.md](criteria-export.md).

It does **not** evaluate individual applicants. Computing
`AdmissionResult.calculated_score` / `is_criteria_passed` lives outside this
app (`appl/models.py`, `backoffice/views/projects.py`, and various
`scripts/`). The applicant side reaches criteria only indirectly, e.g.
`appl.models` `Major.get_admission_criterias()` resolves an applicant's
`cupt_full_code` → `MajorCuptCode` → `CurriculumMajor` →
`curriculum_major.admission_criterias.filter(is_deleted=False)`. So think of
this app as the **authoring + publishing** side.

## Data model

Models live in `criteria/models/` (re-exported from
`criteria/models/__init__.py`).

- **`AdmissionCriteria`** (`admission_criteria.py`) — one versioned criteria
  record, scoped to `(admission_project, faculty)`. Key fields:
  - `version` (int), `is_deleted` (bool — soft delete / retired version),
    `is_from_last_year` (bool), `created_at`, `created_by` (username str).
  - `additional_description`, `additional_condition` — free-text
    supplements **not editable via the criteria form**; set only by the
    offline script `scripts/update_admission_criteria_additional_info.py`
    and consumed by the standalone CUPT export scripts
    (`scripts/export_cupt_cur_props.py`,
    `scripts/export_major_criterias_as_json.py`). The in-app `cuptexport.py`
    ignores them.
  - `additional_interview_condition`, `interview_date`,
    `additional_admission_form_fields_json`,
    `additional_admission_upload_fields_json`, `additional_notice` — edited
    via the form (the form-fields, upload-fields and notice ones only when the
    project enables `is_additional_admission_form_allowed` /
    `is_additional_admission_upload_allowed` / `is_additional_notice_allowed`).
  - `additional_admission_upload_fields_json` — JSON list of extra documents
    (`{title, descriptions, is_required, is_late_upload_allowed}`) applicants
    upload according to the criteria; read via
    `get_additional_admission_upload_fields()`. The `is_late_upload_allowed`
    checkbox is only offered when the project sets
    `is_additional_admission_late_upload_allowed` on top of
    `is_additional_admission_upload_allowed`; with the flag off, extraction
    forces every row to `False`, so re-saving clears stale values. Only the
    authoring side plus the read-only index display (see [the project index
    page](#the-project-index-page)) is implemented — no applicant runtime (see
    [uploaded-documents.md](uploaded-documents.md) for the full feature status
    and what remains).
  - `accepted_student_curriculum_type_flags` (default `'*'` =
    `INITIAL_CURR_TYPE_FLAG`) and `accepted_graduate_year_flags` — CSV
    strings of accepted type ids. `'*'` means "not yet set" and is treated
    as "all accepted" (`DEFAULT_TYPE_FLAG = '1,2,3,4,5'`,
    `DEFAULT_GRADUATE_YEAR_FLAG = '1,2'`). Toggled in-place by AJAX
    endpoints (see below), **not** through the create/edit form.
  - `curriculum_majors_json` — denormalized snapshot of the linked majors
    (rebuilt by `save_curriculum_majors()`).
  - `last_year_major_titles` — used by the "import last year's criteria"
    search.
  - Type constants: `STUDENT_CURRICULUM_TYPE_CHOICES` (formal /
    international / vocational / non_formal / GED) and
    `STUDENT_GRADUATE_YEAR_CHOICES` (current / graduated).

- **`ScoreCriteria`** (`score_criteria.py`) — the individual rows of a
  criteria, both `criteria_type='required'` (qualification / min-score
  conditions) and `'scoring'` (weights). Structure:
  - `primary_order` / `secondary_order` — a two-level tree. Rows with
    `secondary_order == 0` are parents; children point at a parent via
    `parent` (self-FK, `related_name='childs'`) and share the parent's
    `primary_order`.
  - `score_type` (e.g. `TGAT`, `GPAX`, `A82Eng`; see
    `criteria_options.py`), `value` (Decimal), `unit`, `description`,
    `relation`.
  - `relation` on a parent group encodes how children combine:
    for required — `OR` (ข้อใดข้อหนึ่ง), `AND`, `SUM`, `MAX`; for scoring —
    `MAX`, `SUM`. `__str__` renders human-readable Thai.
  - Carries its own `version` field (stamped equal to the parent
    `AdmissionCriteria.version` at creation).

- **`CurriculumMajor`** (`curriculum_major.py`) — a major offered by a
  project: `(admission_project, cupt_code, faculty, major)`. Links to
  `AdmissionCriteria` through the join table via a `ManyToManyField`
  (`admission_criterias`). `is_with_some_admission_criteria()` checks for
  any non-deleted criteria (used to guard deletion).

- **`CurriculumMajorAdmissionCriteria`** (`curriculum_major_admission_criteria.py`)
  — the **join table** between a `CurriculumMajor` and an
  `AdmissionCriteria`. Holds `slots` (int) and `add_limit` (str). `add_limit`
  encodes the acceptance-count rule: `'A'` (default), `'B'`, or `'C<n>'`
  (a numeric cap). Helper methods: `add_limit_display()`,
  `add_limit_type_display()`, `add_limit_num()`.

- **`MajorCuptCode`** (`major_cupt_code.py`) — the CUPT/TCAS program+major
  code catalog: `program_code`, `program_type` / `program_type_code`,
  `major_code`, titles, `component_weight_type`. Unique on
  `(program_code, major_code)`. `get_from_full_code()` parses a full code
  back into a record; `get_program_major_code_as_str()` renders it.

- **`AdmissionProjectFacultyInterviewDate`** (`admission_criteria.py`) —
  per `(admission_project, faculty)` interview date. If
  `is_major_specific` is True, each criteria supplies its own
  `interview_date`; otherwise the faculty-level `interview_date` applies to
  all. `get_from()` returns an existing row or an unsaved default; a
  criteria's effective date resolves in `AdmissionCriteria.get_interview_date()`.

- **CUPT export models** (`cupt_export_config.py`, `imported_criteria_JSON.py`)
  — `CuptExportConfig`, `CuptExportLog`, `CuptExportCustomProject`,
  `CuptExportAdditionalProjectRule` and `ImportedCriteriaJSON`. They belong
  to the export pipeline only; see
  [criteria-export.md](criteria-export.md#data-model-export-side-only).

## Versioning: copy-on-write (the important part)

All writes to an `AdmissionCriteria` go through **one** function:
`upsert_admission_criteria` in `criteria/views/__init__.py` (~line 336),
called from both `handle_create_criteria` and `handle_edit_criteria`.

**There is no in-place update of criteria content.** Every save creates a
brand-new `AdmissionCriteria` row. The whole operation runs inside
`transaction.atomic()`.

- **Create** (no existing criteria passed): new record with `version = 1`.
- **Edit** (existing criteria passed): treated as a new version, not a
  mutation:
  1. `version = old.version + 1`
  2. a **new** `AdmissionCriteria` is created and saved
  3. the old one is soft-deleted: `old.is_deleted = True; save()`

So editing produces version *N+1* and retires version *N* via `is_deleted`.
The standalone `delete()` view is also just a soft delete (`is_deleted=True`)
— it creates no new version.

### What is copied forward vs. re-read from the form

On the edit/version-bump path, the new record's fields come from two
sources:

**Carried over from the previous version (copied):**
- `admission_project`
- `additional_description`
- `additional_condition`
- `accepted_student_curriculum_type_flags`
- `accepted_graduate_year_flags`
- `faculty` (from the old record — effectively preserved)

**Re-read fresh from the submitted POST:**
- `additional_interview_condition`, `interview_date`,
  `additional_admission_form_fields_json`,
  `additional_admission_upload_fields_json`, `additional_notice`
- `version` (incremented)

> ⚠️ **Subtleties worth knowing:**
> - On the **create** path, the three "carried" fields
>   (`additional_description`, `additional_condition`,
>   `accepted_student_curriculum_type_flags`) are **not** set from the form —
>   they can only ever be populated by copying from a prior version (or, for
>   the flags, by the toggle endpoints). This is *why* the copy exists: the
>   form can neither display nor re-submit them.
> - `accepted_graduate_year_flags` is copied forward alongside
>   `accepted_student_curriculum_type_flags` — it must be, since the form
>   doesn't re-submit it (it's set only via the AJAX toggle endpoint).
>   Earlier code omitted it, which silently reset it to default on every
>   version bump; that has been fixed.

### Child records are rebuilt, not copied

On each version bump the dependent rows are reconstructed from the POST and
attached to the new criteria:

- **`ScoreCriteria`** — rebuilt from the parsed `required_*` / `scoring_*`
  form keys, stamped with the new `version`. Parents (`secondary_order==0`)
  are `bulk_create`d first, then children are linked to their parent by
  `(criteria_type, primary_order)` and bulk-created.
- **`CurriculumMajorAdmissionCriteria`** — rebuilt from the `majors_*` keys
  (`slots` from the form). One thing **is** carried over from the old join
  rows: **`add_limit`**, copied per `curriculum_major_id`.

Finally `created_by` is set to the acting user and
`save_curriculum_majors()` refreshes `curriculum_majors_json`.

### Form key encoding

`upsert_admission_criteria` parses POST keys by splitting on `_`:
- `required_<order>_<attr>` / `scoring_<order>_<attr>` →
  `ScoreCriteria`. `<order>` is `primary` or `primary.secondary`.
- `majors_<n>_<attr>` → selected-major rows (`id`, `slot`).
Numeric-looking values are coerced to `Decimal`. An empty submission (no
majors and no score criteria) raises `Http404`.

## The project index page

`criteria/index.html` (view `project_index`) is the per-project+round criteria
list staff use to review and edit a faculty's criteria. The table itself is
`include/criteria_table.html`, which also carries all of the page's inline
jQuery (add-limit editing, the curriculum-type / graduate-year AJAX toggles,
the delete confirm, popovers). Columns: สาขาวิชา / จำนวนรับ /
[สัมภาษณ์] / เงื่อนไขขั้นต่ำ / เกณฑ์การพิจารณา / แก้ไข, with `rowspan`
handling many-majors-per-criteria and many-criterias-per-major. Majors with no
criteria are listed at the bottom.

The two criteria columns come from `include/criteria_table_scorecriteria_cols.html`,
which is where the per-criteria extras are rendered into the เงื่อนไขขั้นต่ำ
cell, in order: curriculum-type / graduate-year toggle forms, the required
score list, `additional_description` / `additional_condition`, the questions
card, and the additional-info card.

`criteria_table.html` is shared with `report_index.html`, and
`criteria_table_scorecriteria_cols.html` is included directly by
`report_major.html`, so two context flags shape it:

- `is_edit_link_hidden` — set by read-only includers to drop every edit
  affordance.
- `is_criteria_edit_allowed` — `project.is_criteria_edit_allowed or
  user.is_super_admin`, computed in `project_index`.

**Every edit affordance must test both** (`is_edit_link_hidden or not
is_criteria_edit_allowed`). `report_index` passes neither, so anything that
checks only `is_edit_link_hidden` leaks an edit link onto the report page —
which is exactly what the questions card used to do.

Two *other* context variables are just as load-bearing: the cell reads
`project` (four feature flags) and `admission_round` (a label, and the
`{% url %}` args of the toggle forms). A page that includes the cell without
them silently drops the curriculum-type / graduate-year lines, the questions
card and the หลังหมดเขต column — and passing `project` **without**
`admission_round` is worse than passing neither: the toggle forms render an
`{% url ... project.id admission_round.id ... %}` with an empty argument and
the page 500s with `NoReverseMatch`. (The forms' hidden choices `<div>` is
rendered even when `is_edit_link_hidden` is set; only the แก้ไข toggle is
dropped.) The major report supplies both **per row**
(`project=row.admission_project admission_round=row.admission_round`),
because its rows span several projects and rounds — a page-level context
variable would not do.

### The two extra-content cards

Both live in the เงื่อนไขขั้นต่ำ cell and render nothing when they have no
content, so a plain criteria costs no extra space.

- **`include/scorecriteria_col_additional_form_fields.html`** — the คำถามเพิ่มเติม
  card: the questions from `additional_admission_form_fields_json` as a table
  (`#` / คำถาม / รูปแบบ), plus a แก้ไข (or เพิ่มคำถาม when there are none)
  link to `edit-form-fields`. Gated by
  `project.is_additional_admission_form_allowed` at the include site. Where the
  questions are answered depends on the round, so the subtitle branches on
  `admission_round.is_portfolio_round` — "แสดงใน TCASFolio" vs. "แสดงในระบบ
  KU Admission" — mirroring the authoring form's own branch. When editing is
  not allowed the links go, but the question list stays (it is data); the
  "no questions yet" card is *only* an edit affordance and disappears whole.
- **`include/scorecriteria_col_additional_info.html`** — a card holding two
  collapsed notes on one line, อัพโหลดเพิ่มเติม (with a count) and
  รายละเอียดเพิ่มเติม, each a Bootstrap 4 `collapse` toggle whose panel is
  keyed `additionalUploadFieldsId-<criteria id>` /
  `additionalNoticeId-<criteria id>`. The panels are the upload-field rows
  (with a หลังหมดเขต column only under
  `project.is_additional_admission_late_upload_allowed`) and the
  `additional_notice` text through `linebreaksbr`. No JS of its own —
  Bootstrap's collapse is already loaded via `main/templates/base.html`.

  It deliberately does **not** check
  `is_additional_admission_upload_allowed` / `is_additional_notice_allowed`,
  unlike the questions card: content stored under a flag that has since been
  turned off is precisely the anomaly a manual check should surface, and it is
  what the next edit would silently blank (see the gotcha below). It is
  read-only — these two fields are edited through the full criteria form, so
  there is no edit link and nothing to gate on `is_criteria_edit_allowed`.

## The criteria form UI

`criteria/templates/criteria/create.html` and `edit.html` are near-identical
and render **one** `<form method="post">` whose body comes from two very
different worlds:

1. the **majors + required + scoring tables**, rendered by a React component
   into `<div id="add-criterion-form">`;
2. a stack of **optional server-rendered partials** for the "additional"
   fields, appended after it.

Both write plain `<input>`s into the same form, and the single submit button
posts everything to `upsert_admission_criteria` at once. Nothing here is a
Django `Form`/`ModelForm` — the field names in these templates *are* the API.

### React component (`main/static/react/src/CreateCriterionForm.js`)

- One 685-line file, no bundler and no npm React. It is compiled JSX→JS
  **in place** by Babel: `main/static/react/` holds `package.json` with
  `yarn dev` = `babel --watch src --out-dir .`, and only
  `@babel/preset-react` is applied. Editing `src/CreateCriterionForm.js`
  does nothing until that watcher (or a one-off `yarn dev`) rewrites the
  sibling `CreateCriterionForm.js`, which is what `{% static %}` serves.
  **Commit both files.**
- `React` / `ReactDOM` are loaded from the unpkg CDN by
  `include/criteria_script_and_style.html`; `$` is the page's global jQuery
  (jQuery UI `autocomplete` / `selectmenu` are used heavily). All are
  globals, not imports.
- Server data arrives as `data-*` attributes read once at module scope via
  `document.currentScript`: `data-majors`, `data-selected-majors`,
  `data-required`, `data-scoring`, `data-mode` (`create`/`edit`, currently
  unused beyond commented-out code) and
  `data-is_custom_score_criteria_allowed`, which is compared against the
  **string `'True'`** (it interpolates the raw Python bool repr).
  `data_required` / `data_scoring` are built by `score_criterias_to_data`
  (`value` serialized as `float`), the major list by `majors_to_json`.
- A second set of globals comes from
  `include/criteria_form_option_script.html`: `requiredTags`, `scoringTags`,
  `unitTags`, `hideRequiredSection`, `useComponentWeightType`, plus
  `relationRequired` / `relationScoring` emitted by `criteria_options_as_js`.
  This is where the `PORTFOLIO_SCORING_TAGS` splice happens
  (`prepend ⧺ general_scoring ⧺ test_tags ⧺ append`); when
  `uses_component_weights` is set, scoring collapses to
  `component_type_tags` built from `component_weight_type_choices`.
- Tree: `Form` → `SelectMajors` + `RequiredCriteria` (skipped when
  `hideRequiredSection`) + `ScoringCriteria`. Each section renders
  `PrimaryTopic` / `PrimaryScoringTopic`, which render their own children
  rows inline in a `React.Fragment`.
- **It generates exactly the POST keys documented above** — `majors_{n}_id`,
  `majors_{n}_slot`, `required_{n}_title|value|unit|type|relation`,
  `scoring_{n}_title|value|type|relation`, with children as `{n}.{i}`. The
  hidden `_type` input carries `score_type`, defaulting to `"OTHER"` — that
  default is what later surfaces as `OTHER`/`ERROR-*` in the CUPT export.
- Two switches shape every row:
  - `is_custom_score_criteria_allowed` — true renders a free-text
    `EditableCell` (auto-growing `<textarea>` + jQuery UI autocomplete over
    the tags); false renders a constrained `SelectMenu` limited to catalog
    descriptions. Same project flag that hides the interview-condition
    partial below.
  - `topic.relation === 'MAX'` — in scoring, blanks the per-child value
    input and percentage cell, matching the export's `cal_type=1` handling.
- `EditableCell` and `SelectMenu` both auto-fill the unit field on select by
  string-munging the field `name` (split on `_`, replace the last segment
  with `unit`) and writing `unitEl.value` through jQuery — i.e. mutating a
  React-rendered input from outside React. Duplicated in both components
  (one carries a `TODO: refactor this`).
- Both templates delete the form and the submit button outright on IE and
  show a Thai "unsupported browser" message.

### Additional-fields partials (`criteria/templates/criteria/include/`)

Server-rendered, included in the same form in this order:
`additional_form_fields` → `additional_notice_form` →
`additional_upload_fields` → `interview_date_form` →
`additional_interview_condition_form`. Each is entirely wrapped in its own
gate, so when a gate is off **no input is rendered and no key is posted**.

| Partial | Model field | Gate |
| --- | --- | --- |
| `additional_form_fields.html` | `additional_admission_form_fields_json` | `has_additional_form_fields` ← `project.is_additional_admission_form_allowed` |
| `additional_upload_fields.html` | `additional_admission_upload_fields_json` | `has_additional_upload_fields` ← `project.is_additional_admission_upload_allowed` (its late-upload column has a second, nested gate `has_additional_late_upload_fields` ← that flag **and** `is_additional_admission_late_upload_allowed`) |
| `additional_notice_form.html` | `additional_notice` | `project.is_additional_notice_allowed` (read directly, not via context var) |
| `additional_interview_condition_form.html` | `additional_interview_condition` | `not project.is_custom_score_criteria_allowed` |

The `has_*` context vars are set in `additional_fields_context`
(`criteria/views/__init__.py`) straight from the project flags.

The two **row-based** partials (form-fields, upload-fields) are copy-paste
twins differing only in prefix and columns:

- form-fields — หัวข้อ + ขนาด, prefix
  `additional_admission_form_fields-{n}-`. `size` is one of `short`
  (คำตอบสั้น), `paragraph` (ข้อความยาว) or `paragraphimage` (ข้อความยาว+รูป);
  see the note below before adding another;
- upload-fields — หัวข้อ + คำอธิบาย + บังคับ (checkbox `value="1"`) +
  อัพโหลดหลังหมดเขต (a second checkbox, rendered only under the nested
  `has_additional_late_upload_fields` gate — header cell, both row variants,
  the `+` row's filler `<td>`, the JS row template and
  `renumberAdditionalUploadFields()` all branch on it; ticking it raises a
  `confirm()` asking whether the late upload is really needed — unticking does
  not), prefix
  `additional_admission_upload_fields-{n}-`.

Both use a **1-indexed, dash-separated** naming scheme
(`prefix-{n}-attr`) — note this is *not* the underscore scheme the React
side and `upsert_admission_criteria`'s splitter use. Both ship inline jQuery
with a `+` row that appends a hardcoded template row and a `renumber…()`
that rewrites the counter cell and every `name` attribute, skipping the
trailing button row; add/delete handlers are delegated and `return false`.

The form-fields table is capped at **5 questions, client-side only**. The
limit lives in a single `{% with max_form_fields=5 %}` in the partial,
feeding both the Thai help text and a `MAX_ADDITIONAL_FORM_FIELDS` JS const,
so the promise and the enforcement cannot drift; because it is
template-local it covers all three includers with no view changes.
`updateAdditionalFormFieldsAddButton()` disables the `+` button and reveals
a `.additional-form-fields-limit-message` notice when the row count (DOM
rows minus the trailing button row) reaches the limit; it runs on ready and
at the end of `renumberAdditionalFormFields()`, which already fires after
every add and delete. `addNewFormRow()` re-checks the limit itself.
Deliberate consequences: rows are counted from the DOM, so five blank rows
block the button even though the server drops blank titles; criteria that
already exceed the limit still render and still post, with the button
disabled until enough rows are deleted; and **the server does not enforce
the cap at all** (`extract_additional_admission_form_fields_as_json` takes
whatever is posted), so a replayed POST or edited DOM can exceed it. The
upload-fields table has no cap.

### Adding a new `size` value (five places, all outside this app)

`size` is a free string carried verbatim from the criteria JSON to the
applicant's answer box. Nothing validates it, so a value the runtime does
not recognise fails silently. All five touch points:

1. `criteria/include/additional_form_fields.html` — three `<select>`s
   (existing rows, the `{% empty %}` row, **and the JS row template inside
   `addNewFormRow()`**; missing the third means new rows lack the option).
2. `criteria/include/scorecriteria_col_additional_form_fields.html` — the
   read-only "รูปแบบ" column, an `if/elif` chain that renders blank for an
   unknown value.
3. `scripts/update_major_additional_notice_and_form.py` — copies `size`
   into `MajorAdditionalAdmissionFormField.size` (`CharField(max_length=20)`)
   with no validation; nothing to change unless the value exceeds 20 chars.
4. `appl/models.py` `MajorAdditionalAdmissionFormField.text_size()` —
   `'short'` → 220, **else** → 2050, so any new value silently inherits the
   paragraph length limit.
5. `appl/templates/appl/include/major_form_field_modal.html` — the applicant
   answer modal. Another `if/elif` with **no `else`**: an unrecognised size
   renders a modal with no input at all and the applicant simply cannot
   answer.

> ⚠️ `paragraphimage` is authored as "ข้อความยาว+รูป" but **the image half
> does not exist**. `ApplicantAdditionalAdmissionFormValue.value` is a plain
> `TextField`, `appl.views.major_additional_form` reads only
> `request.POST['answer']` and never `request.FILES`, and the staff readers
> (`backoffice/views/reports.py`, `projects.py`) treat the value as text. It
> currently renders as a plain long answer.
>
> **Do not build image support into the `appl` side.** As of 2026-07 the
> applicant-facing runtime for these questions (points 3–5 above:
> `MajorAdditionalAdmissionFormField`,
> `ApplicantAdditionalAdmissionFormValue`, `appl.views.major_additional_form`
> and the answer modal) is slated for **removal** — the questions are to be
> answered in TCASFolio instead, which is what the authoring help text
> already tells staff. The authoring side in this app stays; the `appl`
> rendering is the part going away.

`additional_form_fields.html` additionally honours
`shows_additional_form_fields`, set only by the standalone
`edit_additional_admission_form_fields` view (`edit-form-fields`) to
force-open the panel; on create/edit the inline `style` gate governs
instead. The two single-field partials hide themselves with
`{% if value == '' %}`, which does not catch `None`.

## Views & URLs

Namespaced `backoffice:criteria:*` (see `criteria/urls.py`). All are
`@user_login_required` and gated by `can_user_view_project` /
`is_admission_admin`. Faculty scoping is handled by `extract_user_faculty`
(admission admins see all faculties; campus admins see their campus; a
faculty user is pinned to their own faculty).

**Two different faculty questions — don't mix them up.**
`extract_user_faculty` answers *which faculty is currently selected in the
UI*: it reads `?faculty_id=` and, when that is absent, falls back to
`faculty_choices[0]` — an arbitrary faculty. It also returns `None` when a
campus admin asks for a faculty outside their campus, so its result is not
safe to dereference. Authorization is a separate question, answered by
`can_user_edit_faculty(user, faculty)` against the faculty of the object
being edited (admission admin → any; campus admin → same campus; otherwise
the user's own faculty). Every write endpoint (`edit`, `delete`,
`edit-form-fields`, the three AJAX toggles, `update-faculty-interview-date`)
uses the latter. Comparing the selected faculty against the object's faculty
instead — which they all used to do — locks campus admins out of every
faculty but the first, because most of those URLs carry no `?faculty_id=`.
`edit` / `delete` additionally re-point `faculty` at
`admission_criteria.faculty` after the check, so the major list and the
redirect query follow the criteria rather than the selection.

**Authoring**
- `project-index` (`project_index`) — the main per-project+round criteria
  list for a faculty; rows are assembled by `prepare_admission_criteria`.
- `create` / `edit` / `delete` — the versioning flow above. `create`
  supports pre-filling via `?duplicate_score_id=` (import another criteria's
  scores) and `?selected_major_id=&slots=`.
- `edit-form-fields` (`edit_additional_admission_form_fields`) — a targeted
  page for editing just the additional applicant-form questions of an
  existing criteria. The whole view `HttpResponseForbidden`s when the
  project does not set `is_additional_admission_form_allowed`, and again when
  `(not project.is_criteria_edit_allowed) and (not user.is_super_admin)` —
  the same guard `handle_create_criteria` / `handle_edit_criteria` apply, and
  it covers both the GET render and the POST. Otherwise POST saves
  `additional_admission_form_fields_json` **in place on the existing row — no
  version bump**, unlike everything else in this app (`'cancel'` in POST
  redirects back to the project index instead).

**In-place AJAX toggles (mutate the existing criteria, no new version)**
- `update-add-limit` — set a join row's `add_limit` (validated `A`/`B`/`C<n>`).
- `update-accepted-curriculum-type` — `toggle_accepted_curriculum_type`.
- `update-accepted-graduate-year` — `toggle_accepted_graduate_year`.
- `update-faculty-interview-date` — set/clear the faculty-level date.

**Curriculum-major management**
- `curriculum-majors` / `curriculum-majors-toggle` — select/unselect which
  `MajorCuptCode`s exist as `CurriculumMajor`s for a project+faculty (a
  major can only be unselected if it has no criteria attached).
- `list-curriculum-majors` — cross-project matrix of majors per round.

**Reports**
- `report-index` (`report/`) — the landing page for the cross-project
  criteria reports, and the only link to them from the backoffice index
  (labelled รายงานเกณฑ์). It links `report-upload-fields` /
  `report-form-fields` and shows one statistics row per project: criteria
  count, `CurriculumMajor` count, and how many criteria store
  `additional_admission_{form,upload}_fields_json`. Projects listed are
  `is_available OR is_visible_in_backoffice` — the same set the CUPT export
  page uses. ⚠️ Its template is **`criteria/reports.html`**, not
  `criteria/report_index.html`, which was already taken by `project_report`.
  `get_criteria_report_project_stats` does the whole table in **two
  aggregate queries** merged onto the project list in Python, so a project
  with no criteria still gets a zero row. The two additional-fields counts
  are "criteria that store something" — what the `['', '[]']` DB filter can
  answer — deliberately *not* a preview of the reports' row counts, which
  are one per (criteria, major).
- `project-report`, `major-report`, `report-num-slots`,
  `report-num-slots-by-faculty` — read-only slot/criteria summaries
  (`report_num_slots` sums `slots` across projects per faculty/major).
  `major_report` is per **`MajorCuptCode`**, not per project+round: it lists
  every `CurriculumMajor` with that cupt code across all projects, sorted by
  round then `display_rank`, so each row carries its own `admission_project`
  / `admission_round`. Reaching it takes three clicks — backoffice index →
  รายงานจำนวนรับและเกณฑ์ตามคณะ (`report-num-slots`, round hardcoded to 1 in
  that link) → the faculty folder icon → the major folder icon. It
  prefetches `admission_project__admission_rounds`; without that, the sort
  key and the per-row round lookup cost two queries per major.
- `report-form-fields` / `report-upload-fields` — the two
  additional-fields reports, see below. Reached from `report-index`; they
  are no longer linked directly from the backoffice index.
- `report-multiple-criteria-majors` (`report/multiple-criteria-majors/`,
  สาขาที่มีมากกว่า 1 เกณฑ์) — every `CurriculumMajor` holding **more than one
  non-deleted** `AdmissionCriteria`, grouped by project, major-first, with
  each criteria rendered through the same
  `criteria_table_scorecriteria_cols.html` include `report_major` uses
  (`is_edit_link_hidden=True`, which also suppresses the curriculum-type
  toggle, so the page is read-only). This is exactly the CUPT export's
  **"Too many rows"** condition — the export emits one row per (criteria,
  major), so these majors need a `custom_projects` rule to give each row a
  distinct project id — and the page says so with a link to the export page.
  Same project set as `report-index`.
  ⚠️ `get_multiple_criteria_major_rows` prefetches down to
  `…__admission_criteria__scorecriteria_set__childs`. That last hop is not
  optional: `cache_score_criteria_children()` only saves the `has_children`
  lookup, while `scorecriteria_list.html` iterates `childs.all`. With the
  full chain the page costs 6 queries for 141 majors / 323 criteria; without
  it, one query per parent criteria.

### The additional-fields reports

`report/form-fields/` and `report/upload-fields/` (i.e.
`/backoffice/criteria/report/{form,upload}-fields/`) list **every**
non-deleted `AdmissionCriteria` that stores
`additional_admission_form_fields_json` /
`additional_admission_upload_fields_json`, across all projects and years —
the cross-project view the per-project criteria pages cannot give.

`ADDITIONAL_FIELDS_REPORT_TYPES` in `criteria/views/__init__.py` is the only
difference between the two: field name, getter name, Thai title, the
project flag that gates the feature, and the template that renders the field
list. `additional_form_fields_report` / `additional_upload_fields_report` are
thin wrappers over the shared `additional_fields_report`, so a third
JSON-field report would be a dict entry plus a template.

- **Rows** are one per **(criteria, curriculum major)** — a criteria covering
  several majors appears once per major — sorted by round → `display_rank` →
  project id → faculty title → `program_type_code` → `program_code` →
  `major_code`, with projects separated by an `{% ifchanged %}` band and the
  `#` restarting inside each project. A criteria attached to no major still
  gets one row ("ไม่ระบุสาขา"), sorted last in its group.
- The **DB filter can only exclude `''` and `'[]'`**, so rows are filtered
  again in Python on the getter's parsed output (it drops blank-title entries
  and swallows malformed JSON). What survives the DB filter but parses to
  nothing is listed at the bottom under ข้อมูลผิดรูปแบบ with its raw stored
  value, rather than disappearing — that is an authoring bug worth seeing.
- A **โครงการปิดการใช้งานแล้ว** badge marks rows whose project flag
  (`is_additional_admission_form_allowed` /
  `is_additional_admission_upload_allowed`) has since been turned off. The
  data is still stored, and the next criteria edit blanks it silently — same
  reasoning as the additional-info card on the criteria page.
- **แสดงเกณฑ์** expands a per-row Bootstrap `collapse` holding the full
  required / scoring criteria in two columns
  (`include/report_criteria_scores.html` → the shared
  `scorecriteria_list.html`). It is rendered inline, not fetched: with
  `prefetch_related('scorecriteria_set__childs')` over the already-filtered
  criteria, all the score criteria and their children cost **two** queries
  for the whole page. The collapse target is keyed on
  `<criteria id>-<join row id>`, because one criteria can occupy two rows and
  a shared id would toggle both. A small script flips the button label to
  ซ่อนเกณฑ์ on `show.bs.collapse`.
- The whole page is ~7-8 queries. Templates:
  `report_additional_fields.html` plus
  `include/report_form_fields_table.html`,
  `include/report_upload_fields_table.html` and
  `include/report_criteria_scores.html`. The field-list includes are new
  rather than reused: the criteria page's cards are collapsed, carry edit
  affordances and depend on `project` / `admission_round`, none of which a
  report wants.

Both are linked from the backoffice index's พิจารณา: line, which renders
only under `is_application_admin` — computed in `backoffice.views.index` as
`user.is_super_admin` alone, so every viewer of the link also passes the
reports' own `is_admission_admin` gate.

**Row assembly helpers** (`prepare_admission_criteria`): caches score-criteria
children, groups majors per criteria, computes free (uncovered) majors,
attaches faculty interview dates, and (for reports) `combine_criteria_rows`
merges majors that end up with a single non-zero-slot criteria.

## CUPT export/import pipeline

Lives in `criteria/views/cuptexport.py` (+ `cuptexport_fields.py` for the
big CSV field lists and `EXAM_FIELD_MAP`), under the `export/*` URLs, all
admin-only. It turns the authored criteria into the two CSVs uploaded to
ทปอ. (conditions + scoring), re-imports submitted CSVs for validation, and
carries a JSON config layer for per-major overrides and custom project ids.

**See [criteria-export.md](criteria-export.md)** for the full description:
the row pipeline, the config format, custom-project re-mapping, portfolio
handling, slot adjustment, the validation page and the known gotchas.

The one coupling to keep in mind while working in *this* document's
territory: `ScoreCriteria.score_type` values are what the export maps to
CSV columns, so adding a tag to `criteria_options.py` without adding it to
`EXAM_FIELD_MAP` breaks the export.

## Score-type catalog

`criteria/criteria_options.py` defines `CRITERIA_OPTIONS` — the tag lists
shown in the criteria editor (general required/scoring tags + the full exam
`test_tags`: TGAT/TPAT, A-Level, English tests, T-scores, etc.). The
template tag `criteria_options_as_js` (`templatetags/criteria_tags.py`)
serializes these to JS, with `EXCLUDED_TAGS` removing GPAX variants for
specific project ids. When adding a new exam/subject, update both
`CRITERIA_OPTIONS` here and `EXAM_FIELD_MAP` in `cuptexport_fields.py` (the
export maps `score_type` → CUPT column).

### Round-specific scoring choices

Extra **scoring** choices can be shown only for portfolio rounds. The gate is
`AdmissionRound.is_portfolio_round()` (`appl/models.py`, currently
`number == 1`) — the criteria app never checks the round number directly.
The choices live in `PORTFOLIO_SCORING_TAGS` in `criteria_options.py`, a
module-level constant (kept **out** of `CRITERIA_OPTIONS` so the
`criteria_options_as_js` emit loop doesn't serialize it) with two lists:
`prepend` (shown at the beginning of the scoring choice list) and `append`
(shown at the end).

`criteria_options_as_js` now takes `admission_round`; via
`get_round_scoring_extra_tags` it emits `portfolio_scoring_prepend_tags` /
`portfolio_scoring_append_tags` JS consts — populated on a portfolio round,
empty arrays otherwise. `criteria/templates/criteria/include/criteria_form_option_script.html`
builds the list as
`prepend ⧺ general_scoring_tags ⧺ test_tags ⧺ append`, so non-portfolio
rounds render an unchanged `scoringTags`. Applies to both create and edit
(shared include).

> These tags are **not** in `SCORING_SCORE_TYPE_TAGS` / `EXAM_FIELD_MAP`, so
> they have no CSV column of their own. For **portfolio projects** they do
> now reach CUPT: the export folds every top-level scoring criteria into the
> `portfolio` / `interview` columns, counting `INTERVIEW` /
> `INTERVIEW_ENGLISH` (or any description containing `สัมภาษณ์`) as interview
> weight — see
> [criteria-export.md](criteria-export.md#the-portfolio--interview-split).
> On any **other** project they still export as nothing (`ERROR-*`, stripped
> or crashing). Note the `PORTFORLIO` score type is misspelled in the
> catalog.

## Tests

`criteria/tests.py` covers the write path (`upsert_admission_criteria`
versioning, the POST-key parsing and the additional-field extractors) and the
index-page rendering (the two extra-content cards and the `edit-form-fields`
permission gates, the latter through real `Client` requests).

Run them with **`python manage.py test criteria.tests`**, not
`python manage.py test criteria`: discovery walks the `criteria/views/`
package and importing it stand-alone trips the circular import between
`criteria.views` and `backoffice.decorators`, producing a spurious
`unittest.loader._FailedTest`. This is also why the existing tests import
`criteria.views` lazily *inside* test methods rather than at module scope —
keep doing that.

Template-level tests render the partial directly with `render_to_string`, so
they assert on the exact Thai label text; renaming a label in a template will
fail them, which is intended.

## Gotchas / notes for future work

- Editing criteria is copy-on-write; anything you attach to a criteria that
  the edit form does not re-submit **must** be added to the copy block in
  `upsert_admission_criteria` or it will be lost on the next edit — this is
  exactly how `accepted_graduate_year_flags` used to get reset before it was
  added to the copy block.
- `is_deleted=True` is used both for "user deleted this criteria" and for
  "this is an old version" — filter on `is_deleted=False` whenever you query
  live criteria.
- Curriculum-type/graduate-year flags and `add_limit` are edited via AJAX
  and mutate the current row in place (no version bump), so they can drift
  from what a given `version` "was" at creation time.
- `additional_description` / `additional_condition` are script-only and
  invisible to the in-app UI and in-app export — see the standalone
  `scripts/export_*` for their only consumers, and
  [criteria-export.md](criteria-export.md#related-standalone-scripts).
- Anything you change about `score_type` values, criteria structure or the
  major/slot join affects what gets sent to ทปอ. — check
  [criteria-export.md](criteria-export.md#gotchas-summary) before changing
  them.
- Anything that offers an edit affordance on the criteria index must check
  **both** `is_edit_link_hidden` and `is_criteria_edit_allowed` — see
  [the project index page](#the-project-index-page). Server-side, the matching
  guard is `(not project.is_criteria_edit_allowed) and (not
  user.is_super_admin)`; a template gate alone is not enough, since the
  `edit-form-fields` URL can be hit directly.
- **Turning a project flag off silently drops stored data on the next
  edit.** The four "additional" fields are in the re-read-from-POST group
  above, which is only safe because their partial renders an input whenever
  the gate is on. Flip `is_additional_admission_form_allowed` (or any of the
  others) off between edits and the partial disappears, the key is absent
  from the POST, and the next version bump blanks the field — the same
  failure mode as the old `accepted_graduate_year_flags` bug.
- Django's `{# ... #}` comment **cannot span multiple lines** — the multi-line
  form is not parsed as a comment and leaks into the page as literal text. Use
  `{% comment %}` for anything longer than one line. There is a live instance
  of this bug at `appl/templates/appl/include/major_form_field_modal.html:18`
  (in the `appl` runtime that is slated for removal anyway).
- The React source and its Babel output are two checked-in copies of the
  same file. Editing `src/` without re-running `yarn dev` in
  `main/static/react/` changes nothing in the browser.
- Known rough edges in `CreateCriterionForm.js`, if you touch it:
  - new topics get `id: Date.now()`, used both as the React `key` and as the
    `findIndex` identity — two rows added in the same millisecond collide
    and corrupt subsequent edits. (Ids loaded from the server are instead
    order strings like `"1"` / `"1.2"`.)
  - the five row-delete buttons (`SelectMajors` line ~83, and the primary +
    secondary `-` in `PrimaryTopic` / `PrimaryScoringTopic`) have no
    `type="button"` and their handlers never call `preventDefault()` —
    unlike the add handlers, which do. A `<button>` inside a form defaults
    to `type="submit"`, so on paper these should submit the criteria form
    rather than just remove a row. **They were tested in the browser
    (2026-07) and delete works correctly**, so something cancels the
    submit; nothing in the page or `backoffice/base.html` intercepts it.
    The likeliest explanation is HTML5 constraint validation — the form is
    full of `required` fields (e.g. a major added from the autocomplete has
    no `slot`, leaving `majors_N_slot` empty and invalid), and a submit on
    an invalid form is cancelled before navigation while `onClick` still
    runs. If that is the mechanism the safety is **conditional**: deletes
    would begin submitting once every required field is filled. Adding
    `type="button"` to the five buttons would make it unconditional.
    `SelectMajors`' "ลบ" also carries a bogus `htmltype="button"` attribute
    — not a real DOM attribute, so it does **not** set the button type;
    React just passes it through to the HTML. Someone clearly hit this and
    reached for an Ant-Design-style prop name that does not apply here.
  - `SelectRelation` / `SelectMenu` mix controlled `value=` with
    `<option selected>`, which React warns about.
  - `SelectMajors` keeps a `jRef` written during render as a workaround for
    the jQuery autocomplete callback closing over stale state.
