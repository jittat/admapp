# CUPT Criteria Export

This document describes the **CUPT/ทปอ. export pipeline**: the code in
`criteria/views/cuptexport.py` (+ `criteria/views/cuptexport_fields.py`)
that turns the criteria authored in the `criteria` app into the two CSV
files uploaded to the central TCAS system, plus the import/validation
tooling around it.

For how criteria themselves are authored, versioned and stored, see
[criteria.md](criteria.md). This document assumes you already know
`AdmissionCriteria`, `ScoreCriteria`, `CurriculumMajor` and
`CurriculumMajorAdmissionCriteria`.

It is a point-in-time code reading — verify against current code.

## What gets produced

Two CSVs, both admin-only downloads, both generated across **all** visible
projects at once (not per project):

| File | View / URL | Contents |
| --- | --- | --- |
| `conditions-<timestamp>.csv` | `export_required_csv` — `export/required/csv/` | one row per (project, curriculum major): slots, add-limit, accepted student types, interview date, portfolio questions, and every **minimum score** column (`min_*`) |
| `scoring-<timestamp>.csv` | `export_scoring_csv` — `export/scoring/csv/` | one row per (project, curriculum major): the **scoring weights** per exam column, plus the `cal_*` MAX-group columns |

Each run also writes a `CuptExportLog` row (filename + all collected
messages), which is the only place export warnings are persisted — the
response itself is the CSV, so the messages never appear in it. The export
index lists the latest few runs and links each to its admin page (see
[The export log list](#the-export-log-list)); the messages themselves are
only readable in the Django admin.

The required export additionally accepts
`?adjustment=true[&diff=true]`, which re-applies post-publication slot
adjustments (see [Slot adjustment](#slot-adjustment)) and changes the
filename to `conditions-adjusted[-diff]-<timestamp>.csv`.

## Views & URLs

All live under `export/*` in `criteria/urls.py`, namespaced
`backoffice:criteria:*`, all `@user_login_required` **and** gated on
`user.profile.is_admission_admin` (non-admins are redirected to the
backoffice index, not 403'd).

| URL name | View | Purpose |
| --- | --- | --- |
| `export-index` | `index` | landing page: download links, the latest export logs, the CSV re-import form, the config paste form, and a link to the validation page for every project+round |
| `export-logs` | `export_logs` | AJAX refresh of the log list (an HTML fragment, not JSON) |
| `export-required-csv` | `export_required_csv` | conditions CSV |
| `export-scoring-csv` | `export_scoring_csv` | scoring CSV |
| `export-project-validate` | `project_validation` | per project+round validation table |
| `export-import-file` | `import_file` | upload a previously-exported CSV into `ImportedCriteriaJSON` |
| `export-import-config` | `import_config` | paste-import custom projects / project rules |

Templates: `criteria/templates/criteria/cuptexport/index.html`,
`validate.html` and `include/log_list.html`.

## Data model (export-side only)

In `criteria/models/cupt_export_config.py` unless noted; all registered in
`criteria/admin.py`, and the JSON fields are the intended editing surface —
there is no dedicated UI for them beyond the paste-import. The *authored*
models these read from (`AdmissionCriteria`, `ScoreCriteria`,
`CurriculumMajor`, `CurriculumMajorAdmissionCriteria`) are described in
[criteria.md](criteria.md#data-model).

- **`CuptExportConfig`** — `(admission_project, config_json)`. The JSON is
  the per-project export config; a config whose top level is `{"GLOBAL":
  {...}}` applies to **every** project instead. `clean()` validates the
  JSON, so admin edits can't save garbage (direct writes still can).
- **`CuptExportCustomProject`** — `(cupt_code, title)`. An extra CUPT
  project id (e.g. `C2805` "Admission (ใช้คะแนน TPAT3)") that does not
  correspond to an `AdmissionProject`. Used when ทปอ. requires one KU
  project to be split into several project ids by criteria content.
- **`CuptExportAdditionalProjectRule`** — `(admission_project,
  program_major_codes, custom_project, rule_json)`. The rule that decides
  *which* rows get re-mapped onto a custom project.
  `program_major_codes` is a comma-separated list of program+major codes
  (project prefix stripped); `rule_json` is the match condition
  (see [Custom project re-mapping](#custom-project-re-mapping)).
- **`CuptExportLog`** — `(output_filename, message, created_at)`, newest
  first. One row per export run; surfaced by
  [the export log list](#the-export-log-list).
- **`ImportedCriteriaJSON`** (`criteria/models/imported_criteria_JSON.py`) —
  `(criteria_type, project_id, program_id, major_id, data_json)`. A CSV row
  that was previously submitted to (or received back from) CUPT, re-imported
  so the validation page can diff it against what the app would export now.

Two supporting models from elsewhere:

- **`MajorCuptCode`** (`criteria/models/major_cupt_code.py`) — the
  program/major code catalog. `get_program_major_code_as_str()` renders
  `program_code` or `program_code + '0' + major_code`, which is the key
  format used everywhere in the config JSON.
- **`AdjustmentMajorSlot`** (`backoffice/models.py`) — post-publication slot
  changes, keyed by `cupt_code` (the *full* code: project + program +
  major).

## Codes and keys — read this first

Four different "codes" appear in this pipeline and mixing them up is the
main source of confusion:

- `AdmissionProject.cupt_code` — a short project code such as `C28`. Its
  **first letter encodes the TCAS round** (`A`→1, `B`→2, `C`→3, `D`→4);
  `get_project_type` turns it into the CSV `type` column as
  `<round>_<settings.ADMISSION_YEAR>` (falling back to `'2566'` if the
  setting is missing), and an unrecognised first letter yields `''`.
- `MajorCuptCode.program_code` / `major_code` — the CSV `program_id` /
  `major_id` columns.
- **program+major code** — `program_code` (+ `'0'` + `major_code` when there
  is a major). This is the key of `custom_projects` and part of the
  `custom_comments` / `custom_options` keys.
- **project id** — the CSV `project_id` column. Normally
  `project.cupt_code`, but re-mapped to a `CuptExportCustomProject.cupt_code`
  (e.g. `C2805`) by the custom-project rules.

`custom_comments` / `custom_options` keys are `"<program+major>-<project
id>"`, split on `-` in `export_options_as_dict`.

## The export config JSON

`load_export_config(project)` builds one merged dict from **all**
`CuptExportConfig` rows:

1. every row is parsed; a row whose top level is `GLOBAL` contributes
   `config['GLOBAL']` to *all* projects, any other row is skipped unless it
   belongs to `project`;
2. per key, values are merged with `+=`;
3. `CuptExportCustomProject` rows are appended to `projects` as
   `[cupt_code, title]` pairs;
4. `CuptExportAdditionalProjectRule` rows for this project are expanded into
   `custom_projects[<program+major code>]` lists, each entry being
   `{'project_id': <custom project code>, **rule_json}`.

> ⚠️ Step 2 uses `config[k] += this_config[k]`, which works for lists but
> **raises `TypeError` for dicts**. `custom_projects`, `custom_comments`,
> `custom_options` and `additional_folio_criteria` are dicts, so a given key
> may only appear in **one** config row across the whole table (e.g. `GLOBAL`
> *or* the project's own row, never both). JSON parse errors are collected
> under `errors` and shown on the validation page.

Recognised keys (samples live in `criteria/views/export-config*.json`, one
per admission year):

| Key | Shape | Effect |
| --- | --- | --- |
| `projects` | `[[project_id, title], ...]` | catalog of extra project ids and their Thai titles; used to fill `project_name_th` after a re-map |
| `custom_projects` | `{program+major: [rule, ...]}` | re-map rules, see below |
| `custom_comments` | `{"prog-project": "ข้อความ"}` | sets the `condition` column |
| `custom_options` | `{"prog-project": {...}}` | `accepts_male_only: 1` → `gender_male_number = slots`; `custom_values: {field: value}` → set arbitrary CSV columns |
| `additional_folio_criteria` | `{"prog-project": "ข้อความ", "*": "ข้อความ"}` | appends text to the `folio_criteria` column, see below |
| `interview_percents` | `{"<project pk>": [{full_code, porfolio, interview}]}` | per-major portfolio/interview weights for portfolio projects (note the misspelled `porfolio` key, which the code reads verbatim) |

`interview_percents` is keyed by the **numeric `AdmissionProject.id` as a
string**, unlike everything else here.

## The row pipeline

Both exports share the same skeleton:

```
load_all_criterias()                # once, all projects
  └─ per project (is_visible_in_backoffice=True)
       extract_condition_rows / extract_scoring_rows
         └─ extract_rows(convert_to_base_row, extract_f, postprocess_f)
       update_project_information(project, rows)   # config: re-map, comments, options
       fill_zero_min_scores / fill_zero_scoring_scores
sort_csv_rows(all rows)
[update_slots]                      # conditions + ?adjustment=true only
write_condition_row / write_scoring_row  per row
CuptExportLog.save()
```

**`load_all_criterias()`** loads every non-deleted `AdmissionCriteria`
across all projects in a handful of queries, attaches
`criteria.curriculum_major_admission_criterias` by hand (with
`curriculum_major` and `cupt_code` pre-joined), caches score-criteria
children and runs the extraction eagerly, storing
`criteria.extracted_required_criteria` / `.extracted_scoring_criteria` as
`(items, messages)` tuples. It returns a `defaultdict(list)` keyed by
project id. Every consumer downstream reads those two attributes rather than
re-extracting.

**Scoring** extraction runs for every criteria; **required** extraction only
for projects where `zeroes_score_fields(project)` is false. So on such a
project `extracted_required_criteria` simply **does not
exist** — every reader of it is behind the same predicate.

> ⚠️ **Scoring extraction now runs for every criteria** (2026-08). It used to
> be skipped for `is_cupt_export_only_major_list` projects, whose rows carry
> no criteria columns. It cannot be any more:
> [`preprocess_portfolio_admission_criteria`](#portfolio-projects) derives
> the portfolio/interview split from the authored scoring criteria, and most
> portfolio projects *are* only-major-list projects. `project_validation`
> now mirrors this branch, so the export and the validation page agree.
> Consequences that have **not** been worked through yet:
>
> - scoring extraction is paid for on every project, exported or not;
> - warnings raised by criteria that are never exported now reach
>   `CuptExportLog`;
> - `check_other_score_type` used to `KeyError` on a `score_type` with no
>   catalog entry — including the portfolio-round tags. It now reports
>   `UNKNOWN-SCORETYPE` instead, because a crash there would take down both
>   CSV exports.

**`convert_to_base_row`** produces the common columns:
`project_id` (`project.cupt_code`), `project_name_th`
(`project.short_title`), `program_id`, `major_id`, `add_limit`
(`mc.add_limit_display()`), `type` (`get_project_type`), plus three
non-CSV working keys — `criteria`, `curriculum_major`, `slots` — that the
writers strip again. For grouped-row projects `add_limit` is forced to `0`.

### The two export flags

Two `AdmissionProject` flags shape the export, and **no code reads them
directly** — every branch goes through one of two predicates, which is what
keeps the concerns separable:

| predicate | true when | what it decides |
|---|---|---|
| `uses_grouped_major_rows(project)` | `is_cupt_export_only_major_list` | one combined row per major (`combine_slots`), `criteria` is `None` on validation rows, `add_limit` forced to `0`, and the scoring CSV skips the project entirely unless it is a portfolio project |
| `zeroes_score_fields(project)` | either flag | no required extraction, so no `min_*` / `score_condition` / `subject_names` / `score_minimum`; and of the scoring criteria only `PORTFOLIO_SCORE_TYPES` (`R1_PORTFOLIO` / `R1_INTERVIEW`) reaches a column |

**`is_cupt_export_only_major_list`** (default **True**) means "send ทปอ. only
the list of majors, no criteria" — it implies both predicates.
`combine_slots` sums `slots`, mutates and returns the *first* row, and drops
the rest.

**`is_cupt_export_zero_score_fields`** (default **False**) is the half-way
case: rows stay per-criteria and `add_limit` is normal, but every score
exports as `0`. Portfolio projects still export their portfolio/interview
split, because `preprocess_portfolio_admission_criteria` has already reduced
their scoring criteria to exactly those two score types.

> `cal_type` / `cal_score_sum` / `cal_subject_name` are **not** in
> `SCORING_FILE_SCORING_ZERO_FIELD_STR`, so `scoring_extract_f` must keep
> setting them to `0` explicitly when it skips the weights — an absent key is
> written as an empty cell, not a zero.

### Conditions: `extract_condition_rows`

Per row, `condition_extract_f`:

- walks `extracted_required_criteria[0]`; each plain item becomes
  `min_<field> = <value>` via `exam_name_to_required_field`;
- an `OR` group becomes the triple `score_condition = 1`,
  `subject_names = '<field> <field> ...'`,
  `score_minimum = '<v> <v> ...'` (space separated). Only **one** `OR`
  group per criteria is supported — a second logs `ERROR: Too many ORs`;
- `extract_interview_dates` → `interview_date` from
  `AdmissionCriteria.get_interview_date_str()` (which resolves the
  faculty-level `AdmissionProjectFacultyInterviewDate` unless it is
  `is_major_specific`);
- `extract_student_curriculum_type` → `only_formal` / `only_international` /
  `only_vocational` / `only_non_formal` / `only_ged`, each **`1` = accepted,
  `2` = not accepted** (not a boolean);
- `extract_portfolio_information` → the `folio_*` columns, see below.

`write_condition_row` then fills `receive_add_limit` from `add_limit`,
`receive_student_number` from `slots`, and `description` from
`"<faculty> <major cupt code>"`, applies `CONDITION_FILE_FIELD_DEFAULTS`
(notably `interview_location = 'มหาวิทยาลัยเกษตรศาสตร์'` and
`link = 'https://admission.ku.ac.th/'`) and zero-fills the rest.

> There is a deliberate hack: if the row *already* carries
> `receive_student_number` (only possible via `custom_values`), the
> slots-derived value is dropped so the custom number wins.

### Scoring: `extract_scoring_rows`

Per row, `scoring_extract_f`:

- each plain item of `extracted_scoring_criteria[0]` becomes
  `<field> = <base_weight>` via `exam_name_to_scoring_field`;
- a `MAX` group becomes `cal_type = 1`, `cal_score_sum = <group weight>`,
  `cal_subject_name = 'f1|f2|...'` (pipe separated). One `MAX` group only —
  a second logs `ERROR: Too many MAXs`.

Projects where `uses_grouped_major_rows` is true are **skipped entirely**
by the scoring export unless they are portfolio projects. A
`zeroes_score_fields` project still gets its row — carrying the
portfolio/interview split, or all zeros if it is not a portfolio project.

`write_scoring_row` strips the working keys plus a handful of
conditions-only columns (`condition`, `gender_male_number`,
`interview_location`, `receive_student_number`, `join_id`) that
`update_project_information` may have set, and zero-fills.

> `SCORING_FILE_FIELD_DEFAULTS` is empty, and the loop that would apply it
> reads from `CONDITION_FILE_FIELD_DEFAULTS` — harmless today, wrong the
> moment someone adds a scoring default.

### Exam → column mapping

`EXAM_FIELD_MAP` in `cuptexport_fields.py` maps `ScoreCriteria.score_type`
to a CSV column base name; conditions prefix it with `min_`. An unmapped
score type — or one mapped to `''` (`GPAX_5_SEMESTER`, `TOEFL_PBT_ITP`,
`OOPT`, `MU_ELT`) — produces the literal key `ERROR-<score_type>`.

Before writing, both exports delete a **hardcoded list** of such keys
(`ERROR-OTHER`, `ERROR-GPAX_5_SEMESTER` for conditions; `ERROR-OTHER`,
`ERROR-INTERVIEW_ENGLISH` for scoring), logging them to the export log.

> ⚠️ Any *other* `ERROR-*` key reaches `csv.DictWriter` as an unknown field
> and raises `ValueError`, i.e. the whole export 500s. Adding a score type
> to `criteria_options.py` without adding it to `EXAM_FIELD_MAP` is exactly
> how that happens.

### Score-type normalization

`ScoreCriteria.score_type` defaults to `OTHER` when the criteria editor
lets staff type free text. `check_other_score_type` (called from both
extractors) tries to recover: it looks the row's **description** up in a
reverse map built from `REQUIRED_SCORE_TYPE_TAGS` /
`SCORING_SCORE_TYPE_TAGS` (whitespace stripped) and rewrites `score_type`
in memory. What it cannot recover stays `OTHER` and is logged. It also logs
`ERROR:MISMATCH-SCORETYPE` when a row's `score_type` and `description`
disagree — that means someone edited the text under a catalog tag.

Rows with `value = None` are logged as `Value=None: <description>`
(except `GPAX`, see `NONE_WARNING_IGNORE_SCORE_TYPES`); rows with
`value = 0` are silently dropped.

> ⚠️ `normalize_int_value(val)` returns `int(val)` when the value is
> integral and **implicitly `None` otherwise**. A non-integer value (e.g.
> `2.5`) is therefore written as an empty cell, silently — or, inside an `OR`
> group's space-joined `score_minimum`, as the literal string `"None"`.
>
> The **conditions** export no longer calls it directly: minimums go through
> `normalize_min_value(field_name, val)`, which skips normalization when the
> column name contains **`gpa`** or **`tscore`** (`NON_NORMALIZED_FIELD_KEYWORDS`)
> — the columns that carry genuine decimals. Consequences: a GPAX minimum of
> `2.75` now exports as `2.75` instead of blank, and an integral one exports
> as `3.0` rather than `3`, since the raw value is passed straight through.
> A non-integral minimum on any *other* column (e.g. `min_ielts 3.5`) is
> still lost — that was left out of scope deliberately.
>
> The **scoring** export still calls `normalize_int_value` unconditionally,
> so an integral `gpax` *weight* keeps exporting as `20`, not `20.0`.

### Portfolio projects

`is_portfolio_project()` tests the criteria's project id against a
**hardcoded list** of ids (`PROJECT_LIST` in `cuptexport.py`); a second
hardcoded list (`R11_LIST`) splits round-1 projects into sub-round 1 vs 2.

For those projects:

- `extract_portfolio_information` writes `folio_q1..q3` and
  `folio_q1_type..q3_type` from the criteria's
  `additional_admission_form_fields_json` — at most **3** questions (extras
  are `print`ed and dropped), blank titles skipped, `size == 'short'` → type
  `'A'`, anything else → `'C'`. Non-portfolio projects get all `folio_*`
  columns zeroed (`folio_criteria` is the exception — it's `''`, not `'0'`,
  for non-portfolio projects);
- `folio_closed_date` comes from `get_portfolio_closed_date`: a per-project
  override table first, then a `(campus_id, sub-round)` table. **Both are
  hardcoded Thai dates in the source** and must be edited each admission
  year;
- `folio_criteria` is the applicant-facing scoring criteria text, via
  `AdmissionCriteria.get_all_scoring_score_criteria_as_numbered_str()`
  (`criteria/models/admission_criteria.py`): each top-level scoring criteria
  numbered `"1. <str(criteria)>"` (percent included), children numbered
  `"1.1 <str(child)>"` indented with 4 spaces. That method wraps the shared
  `criteria_as_str(criteria, numbered=False, hide_percent=False,
  indent_chars='  - ', display_fn=None)` helper — the same function backing
  `get_all_required_score_criteria_as_str` /
  `get_all_scoring_score_criteria_as_str` used elsewhere in this pipeline,
  just with `numbered=True` and a different indent. `display_fn(c)`, when
  given, overrides how an item renders and takes priority over
  `hide_percent`; it exists for
  `scripts/export_majors_from_criteria.py`'s `render_score_criterias`, whose
  `short=True` mode renders via `c.display_with_short_relation()` instead of
  `str(c)` — that script now delegates to `criteria_as_str` rather than
  duplicating the traversal;
- the config's `additional_folio_criteria` then appends free text to that
  column, in `apply_additional_folio_criteria`. Entries are keyed like
  `custom_comments` (`"<program+major>-<project id>"`), plus a `"*"` key
  applied to **every** row; a row matching both gets its own text first and
  the `"*"` text last, each on its own line. The pass runs **last** in
  `update_project_information`, after `custom_options` — which can itself set
  `folio_criteria` via `custom_values` — so the text is always appended to the
  final value. Rows whose `folio_criteria` is empty are skipped, so a `"*"`
  entry never reaches a non-portfolio row; and because scoring rows have no
  `folio_criteria` key at all, that same guard keeps the column out of the
  scoring CSV, whose field list has no `folio_criteria` and whose
  `DictWriter` would raise on it;
- the scoring export replaces the extracted criteria wholesale with two
  synthetic items, `R1_PORTFOLIO` and `R1_INTERVIEW`
  (`preprocess_portfolio_admission_criteria`, see below), and then overrides
  them per major from the config's `interview_percents`.

#### The portfolio / interview split

`preprocess_portfolio_admission_criteria` **derives** the two percents from
what the faculty authored — it does not invent them. Per criteria, over the
items of `extracted_scoring_criteria[0]` (already exactly the top-level
score criteria: `get_all_scoring_score_criteria()` keeps only
`secondary_order == 0`, and a `MAX` group appears as a single `GROUP-MAX`
item carrying the group weight):

- an item is **interview** weight when its `score_type` is `INTERVIEW` or
  `INTERVIEW_ENGLISH`, or its description contains `สัมภาษณ์`;
- `R1_INTERVIEW = round(100 × interview / total)`, `R1_PORTFOLIO = 100 −
  R1_INTERVIEW`, over the total of all top-level weights.

Everything that is not interview weight is portfolio weight, so the two
always sum to 100. The rules were decided deliberately (2026-08):

| Question | Decision | Why |
| --- | --- | --- |
| Rounding | interview rounds to an integer, the **remainder goes to `R1_PORTFOLIO`** | `normalize_int_value` writes a **blank cell** for any non-integral value, so decimals cannot be exported; giving portfolio the remainder keeps the pair at exactly 100 |
| No weights at all (`total == 0`) | export **0 / 0**, with a message in the log | the old fixed 100/0 was a fabricated value; 0/0 is visibly wrong instead of plausibly wrong |
| `MAX` groups | classified by the **group row itself** (its own `score_type` / description), never by its children | a group's children are alternatives, so "some child is an interview" says nothing about the group's weight |
| `interview_percents` config | still overrides, unchanged | it is per major, this is per criteria; the Google-Sheets workflow is untouched by this change |

`is_interview_scoring_item` needs the criteria's **description**, which the
extracted item dicts did not carry before this change; they now include
`description` (and `group_score_type` for `MAX` groups) alongside
`score_type` / `base_weight`.

The rounding and classification live in the pure helper
`compute_portfolio_interview_percents(items) -> (portfolio, interview,
messages)`, which is what `criteria/tests.py`
(`PortfolioInterviewPercentTestCase`) exercises.

### Custom project re-mapping

`validate_project_ids(rows_of_one_major, additional_projects,
cupt_code_custom_projects)` decides the `project_id` of each row when one KU
project must be reported as several CUPT project ids.

For a major with rules configured, each row's required/scoring criteria are
rendered to human-readable Thai strings
(`get_all_required_score_criteria_as_str()` /
`..._scoring_...`) and matched against the rules by `is_criteria_match`:

| Rule key | Meaning |
| --- | --- |
| `score-include` | substring must appear in the scoring criteria string |
| `require-include` | substring must appear in the required criteria string |
| `score-not-include` | substring must **not** appear in the scoring string |
| `require-not-include` | substring must **not** appear in the required string |

The **first** matching rule wins and its `project_id` replaces the row's;
`project_name_th` is then looked up in `additional_projects` (the
`projects` catalog), and a miss is reported as `PROJECT NOT FOUND`.

> ⚠️ Matching is plain substring matching over rendered Thai criteria text.
> Rewording a criteria description silently breaks a rule — the row keeps
> the base project id and two rows can collide on the same `project_id`,
> which is what the "Too many rows" validation message is for.

If a major has **more than one** row and no rules are configured, that is
itself an error (each (project, program, major) must be unique in the CSV)
and is reported on the validation page.

`update_project_information` runs this on the export path (with
`save_criteria_str=False`, so the rendered strings are dropped again) and
then applies `custom_comments` and `custom_options`.

### Sorting and slot adjustment

`sort_csv_rows` orders by `(project_id[:3], program_id, major_id,
project_id)` — i.e. by the *base* project code first, so re-mapped custom
project ids stay grouped with their origin project.

**Slot adjustment** (`update_slots`, conditions export only): with
`?adjustment=true`, rows whose full code (`project_id + program_id [+ '0' +
major_id]`) matches an `AdjustmentMajorSlot` **whose `current_slots` differ
from `original_slots`** get `slots` (and `gender_male_number`, if set)
replaced. With `&diff=true` the export additionally keeps *only* those rows,
producing a delta file to submit.

## The export log list

The export index shows the **5 latest `CuptExportLog` rows** (time,
filename, a link to the row's Django admin change page) as an item of the
"รายการข้อมูล" list. It is rendered by
`criteria/cuptexport/include/log_list.html` from
`load_latest_export_logs(since_id)`, which annotates each log with a
non-model `is_new` attribute (`log.id > since_id`; nothing is new when
`since_id` is `None`). The same helper and partial serve both the initial
page render and the AJAX refresh, so there is one renderer.

`export_logs` (`export/logs/`) re-renders that partial for
`?since=<log id>` and returns the HTML fragment. The page captures the
newest id **once at load** (`data-latest-id` on the table) and sends it as
`since` on every refresh, so a log that arrives while the page is open keeps
its `new` pill until the page is reloaded. A request without `since` — the
initial render — marks nothing as new.

### Knowing when a download finished

The CSV downloads are plain links opening in a new tab, so the page cannot
observe the response. It uses the standard **download cookie** handshake:

1. clicking a download link (class `js-export-download`) generates a random
   token, appends it to that link's href as `dl=<token>`, and clears any
   stale cookie;
2. `export_required_csv` / `export_scoring_csv` call
   `set_download_token_cookie(request, response)` **after** `log.save()`,
   which sets `cupt_export_dl=<token>` (`max_age=600`, not httponly) when
   `dl` is present. Because it runs after the save, seeing the cookie
   guarantees the log row exists;
3. the page polls `document.cookie` every 500 ms; on a match it clears the
   cookie, refreshes the list once, reports `export เสร็จแล้ว` and stops.

A 10-second interval refresh runs in parallel as the fallback (an export
that 500s never sets the cookie, and never writes a log either). Both timers
stop 5 minutes after the click, after one final refresh. `dl` is ignored by
everything else in the export path, so it cannot affect the CSV.

## The validation page

`project_validation(project_id, round_id)` renders one table per project+
round (`cuptexport/validate.html`) with, per (major, criteria) row: the
resolved `project_id`, the codes, slots, `add_limit`, the rendered required
and scoring criteria strings next to the extracted items and their
messages, the **last imported** CSV JSON for that key, and the row's
validation messages. Majors with no criteria at all are listed separately
as "สาขาที่ไม่ระบุข้อมูล".

It runs the same extraction as the export but keeps everything (including
`validation_messages`, which the export path doesn't build). The
imported-CSV side comes from `load_imported_data(criteria_type, project,
field_str, additional_fields)`, which loads `ImportedCriteriaJSON` rows
whose `project_id` starts with `project.cupt_code[:3]`, keeps only the
fields in the relevant zero-field list that are **not** `'0'`, and re-dumps
them as a compact JSON string keyed by `(project_id, program_id, major_id)`.
So the columns you see are "what was submitted, non-zero only" — a quick
eyeball diff against the extracted items in the neighbouring cell, not a
computed diff.

> ⚠️ The page renders the required/scoring criteria strings but **none of the
> `folio_*` columns**, `folio_criteria` included.
> `extract_portfolio_information` runs only on the export path (via
> `extract_condition_rows`), never in `project_validation`, so neither the
> numbered criteria text nor anything appended to it by
> `additional_folio_criteria` can be previewed here — staff have to run the
> export to see the column. **Worth examining later.**

## Importing

- **`import_file`** (POST) — takes `criteria_type` (`required`/`scoring`)
  and an uploaded CSV. It **deletes every existing `ImportedCriteriaJSON`
  row of that type first**, then stores one row per CSV line with the whole
  line as `data_json`. The index page shows the current row counts.
- **`import_config`** (POST) — takes `config_type` and a `config` textarea:
  - `custom-projects`: lines of `["C2801", "ชื่อโครงการ"],` →
    `CuptExportCustomProject` (upsert by `cupt_code`; blank titles skipped);
  - `custom-rules`: lines of
    `["C2805", "C2810020108901001A,C28...", "{\"score-include\": \"Math1\"}"],`
    → `CuptExportAdditionalProjectRule`. The **first 5 characters** of the
    second field are taken as the `AdmissionProject.cupt_code` and stripped
    from every listed code; unknown projects or custom projects are skipped
    silently.

  Both parsers wrap the pasted lines in `[...]` and tolerate a trailing
  comma. They will raise `IndexError` on an empty last line, and the view
  has no error handling — a malformed paste is a 500.

## Field lists (`cuptexport_fields.py`)

Whitespace-separated strings, split at import time. Order matters — it is
the CSV column order required by ทปอ.

| Constant | Role |
| --- | --- |
| `CONDITION_FILE_FIELD_STR` | full conditions header (~230 columns) |
| `SCORING_FILE_FIELD_STR` | full scoring header |
| `CONDITION_FILE_ZERO_FIELD_STR` | non-score conditions columns force-filled with `'0'` at write time (`project_name_en`, gender counts, `join_id`) |
| `SCORING_FILE_ZERO_FIELD_STR` | same for scoring — currently empty |
| `CONDITION_FILE_MIN_ZERO_FIELD_STR` | every `min_*` / qualification column; zero-filled per row *before* writing, and the field list the validation page reads back from imported CSVs |
| `SCORING_FILE_SCORING_ZERO_FIELD_STR` | every scoring weight column, same two uses |
| `EXAM_FIELD_MAP` | `score_type` → column base name |

When ทปอ. changes the file format, these are the constants to update, and
`EXAM_FIELD_MAP` must stay in sync with `criteria/criteria_options.py`
(see [criteria.md](criteria.md#score-type-catalog)).

## Related standalone scripts

`criteria/views/cuptexport.py` is the in-app path. `scripts/` holds a
separate, older family of CUPT exporters run from the command line —
`export_cupt_cur_props.py`, `export_major_criterias_as_json.py`,
`export_majors_from_criteria.py`, `prep_admission_criteria_for_next_year_export.py`,
plus the `check_cupt*.py` / `validate_cupt_results.py` verification tools.
Notably those scripts *do* read `AdmissionCriteria.additional_description` /
`additional_condition`, which the in-app export ignores entirely.

## Gotchas summary

- Export views are **global**: they walk every project with
  `is_visible_in_backoffice=True`, so a half-finished project is included as
  soon as it is visible in the backoffice.
- Warning *messages* only reach `CuptExportLog`; the export page shows that
  a run happened, but reading what it complained about still means opening
  the admin. Check the log after every export.
- `normalize_int_value` turns non-integral values into blanks silently. The
  conditions export works around this for `gpa`/`tscore` columns via
  `normalize_min_value`; the scoring export and every other column still
  drop decimals.
- An unmapped score type crashes the export via `DictWriter`, unless it
  happens to be one of the two hardcoded `ERROR-*` names.
- `load_export_config` cannot merge dict-valued keys across config rows.
- Custom-project rules match on rendered Thai criteria text — fragile by
  construction.
- Portfolio sub-rounds, closing dates and the portfolio project list are all
  hardcoded per admission year in `cuptexport.py`.
- Scoring extraction now runs for **every** criteria, including
  only-major-list projects whose scores are never written — the consequences
  of that are not worked through yet, see the remark under
  [The row pipeline](#the-row-pipeline).
- The portfolio/interview split is rounded to whole percents; a faculty who
  authors a 62.5% weight gets 63/37, silently.
- `import_file` wipes all rows of the chosen type before importing.
- `combine_slots` mutates and returns the first row of the group; the other
  rows (and their criteria) simply vanish from the output.
- The export only ever sees `is_deleted=False` criteria, and criteria
  editing is copy-on-write, so an export run reflects whatever version was
  current at that moment — see
  [criteria.md](criteria.md#versioning-copy-on-write-the-important-part).
