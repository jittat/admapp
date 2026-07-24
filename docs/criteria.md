# Criteria Module

This document describes the `criteria` app: how admission criteria are
modeled, how they are edited with **copy-on-write versioning**, how
curriculum majors are linked, and how the whole thing is exported to the
CUPT/TCAS central system. It is the result of a code-reading session over
the entire app (`criteria/models/`, `criteria/views/__init__.py`,
`criteria/views/cuptexport.py`, `criteria/urls.py`, `criteria_options.py`,
templates). It is a point-in-time analysis — verify against current code.

## What the app is (and isn't)

The `criteria` app is where staff **define and publish** the admission
criteria for each project+faculty: the required conditions (min scores /
qualifications), the scoring weights, which curriculum majors a criteria
applies to, slot counts, interview dates, accepted student types, etc. It
also owns the **CUPT export/import** pipeline that turns those definitions
into the CSV files uploaded to the central admission system.

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
    (`{title, descriptions, is_required}`) applicants upload according to the
    criteria; read via `get_additional_admission_upload_fields()`. Only the
    authoring side is implemented (see
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

- **CUPT export config models** (`cupt_export_config.py`) —
  `CuptExportConfig` (per-project JSON config, or `GLOBAL`),
  `CuptExportLog` (export run log), `CuptExportCustomProject` and
  `CuptExportAdditionalProjectRule` (rules that re-map a curriculum major
  to a custom CUPT project id based on criteria content).

- **`ImportedCriteriaJSON`** (`imported_criteria_JSON.py`) — round-trip
  buffer: rows of a previously-exported CSV re-imported so the validation
  page can diff current criteria against what was last submitted.

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

## Views & URLs

Namespaced `backoffice:criteria:*` (see `criteria/urls.py`). All are
`@user_login_required` and gated by `can_user_view_project` /
`is_admission_admin`. Faculty scoping is handled by `extract_user_faculty`
(admission admins see all faculties; campus admins see their campus; a
faculty user is pinned to their own faculty).

**Authoring**
- `project-index` (`project_index`) — the main per-project+round criteria
  list for a faculty; rows are assembled by `prepare_admission_criteria`.
- `create` / `edit` / `delete` — the versioning flow above. `create`
  supports pre-filling via `?duplicate_score_id=` (import another criteria's
  scores) and `?selected_major_id=&slots=`.
- `edit-form-fields` (`edit_additional_admission_form_fields`) — editing
  additional applicant-form questions (currently mostly disabled — the POST
  path returns `HttpResponseForbidden` except for cancel).

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
- `project-report`, `major-report`, `report-num-slots`,
  `report-num-slots-by-faculty` — read-only slot/criteria summaries
  (`report_num_slots` sums `slots` across projects per faculty/major).

**Row assembly helpers** (`prepare_admission_criteria`): caches score-criteria
children, groups majors per criteria, computes free (uncovered) majors,
attaches faculty interview dates, and (for reports) `combine_criteria_rows`
merges majors that end up with a single non-zero-slot criteria.

## CUPT export/import pipeline

Lives in `criteria/views/cuptexport.py` (+ `cuptexport_fields.py` for the
big CSV field lists and `EXAM_FIELD_MAP`). All views are admin-only.
URLs under `export/*`.

- **`index`** — landing page; shows how many `ImportedCriteriaJSON` rows
  exist per type.
- **`export_required_csv`** / **`export_scoring_csv`** — generate the two
  CSVs uploaded to CUPT. For every visible project they walk all non-deleted
  criteria (`load_all_criterias`), convert each join row to a base row
  (`convert_to_base_row`), and fill in condition/scoring columns:
  - required: `extract_required_criteria` flattens `ScoreCriteria` into
    min-score columns; an `OR` group becomes `score_condition=1` +
    `subject_names` + `score_minimum`. Only **one** `OR` group is allowed.
  - scoring: `extract_scoring_criteria`; a `MAX` group becomes `cal_type=1`
    + `cal_subject_name` + `cal_score_sum`. Only **one** `MAX` allowed.
  - `score_type` values are normalized against `criteria_options.py`
    descriptions (`normalize_score_type`); unknowns surface as
    `OTHER`/`ERROR-*` and are logged.
  - `update_project_information` applies the JSON export config:
    `custom_comments` → `condition`, `custom_options` (e.g.
    `accepts_male_only`, custom values), and custom-project re-mapping via
    `validate_project_ids` / `is_criteria_match`.
  - portfolio projects (`is_portfolio_project`, a hardcoded id list) get
    extra folio columns and interview-percent handling.
  - each run writes a `CuptExportLog` with any messages; optional
    `?adjustment=true[&diff=true]` re-applies `AdjustmentMajorSlot`.
- **`project_validation`** — per-project page diffing current criteria
  against the last-imported CSV (`ImportedCriteriaJSON` via
  `load_imported_data`), surfacing errors before re-export.
- **`import_file`** — upload a previously-exported CSV back into
  `ImportedCriteriaJSON` (replaces all rows of that `criteria_type`).
- **`import_config`** — bulk-load `CuptExportCustomProject` /
  `CuptExportAdditionalProjectRule` rows from pasted JSON-ish lines.

Config precedence in `load_export_config`: a config whose top level is
`GLOBAL` applies to all projects; otherwise a `CuptExportConfig` only
applies to its own project. `CuptExportCustomProject` rows are appended as
selectable `projects`, and `CuptExportAdditionalProjectRule` rows become
`custom_projects` keyed by program+major code.

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

> The entries in `PORTFOLIO_SCORING_TAGS` are currently **placeholder**
> values. They are also not yet wired into CUPT export
> (`SCORING_SCORE_TYPE_TAGS` / `EXAM_FIELD_MAP`) — export for these is planned
> via a separate mechanism.

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
  `scripts/export_*` for their only consumers.
