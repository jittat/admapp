# Major ↔ CUPT code: usage survey and unification plan

Point-in-time analysis (2026-09-14). Verify against current code before
acting on it. **Nothing here has been unified yet** — this is the plan.

## How a `Major` is linked to its CUPT code

There is no foreign key. `appl.Major` stores a string and it is parsed back
into a `criteria.MajorCuptCode` row on demand:

```
Major.cupt_full_code (string)
  └─ MajorCuptCode.get_from_full_code()
       └─ CurriculumMajor(admission_project=major.admission_project, cupt_code=<row>)
            └─ .admission_criterias.filter(is_deleted=False)
```

- `Major.cupt_full_code` format: `program_code` (15 chars incl. the type
  letter, e.g. `10020105301601D`), plus `'0' + major_code` when the program
  has sub-majors. `MajorCuptCode.get_program_major_code_as_str()` renders the
  same format.
- `Major.cupt_code` / `cupt_study_type_code` (and `Faculty.cupt_code`,
  `AdmissionProject.cupt_code`) only feed the legacy fallback in
  `get_full_major_cupt_code()`.
- `CurriculumMajor.major` (FK to `Major`) exists but is **never populated**.

### Where the string comes from

- `scripts/import_majors.py` sets `cupt_full_code` at import time from the
  last two columns of the majors CSV (program code, major code).
- `scripts/update_major_cupt_full_code.py <round_id>` — older path: re-derives
  it from `detail_items_csv[-2:]` for all majors in a round.
- `scripts/import_major_codes.py <csv>` — sets `cupt_code`,
  `cupt_study_type_code`, `cupt_full_code` straight from a CSV.

### What the source data looks like

Survey of `~/Dropbox/adm68–70/project-majors/**/*.csv` (3,962 major rows):

- Program code (second-to-last column) is always 15 chars.
- Major code (last column) is blank (3,345 rows) or a **single letter**
  `A`–`T`. No multi-digit major codes occur, although parsers below assume
  one character and `criteria/tests.py:1405` uses a synthetic `'10'`.
- One file (`adm68/.../109-posn-updated.csv`, 50 rows) is missing the major
  column, so the program code sits in the last column. The
  `len(major_code) > 5` check in the import/update scripts handles this;
  readers of `detail_items_csv[-2:]` do not.

## Usage survey

### App code

| Location | Use |
|---|---|
| `appl/models.py` `Major.get_full_major_cupt_code()` | returns `cupt_full_code`, else builds legacy `'002'+project+faculty+'%03d' major+study_type` |
| `appl/models.py` `Major.get_major_cupt_code()` | parser **A**: `MajorCuptCode.get_from_full_code` (len > 15 → program `[:-2]`, major `[-1:]`) |
| `appl/models.py` `Major.get_admission_criterias()` | via `get_major_cupt_code()` |
| `criteria/upload_documents.py` `get_majors_by_cupt_code_id` | parser A, via `get_major_cupt_code()` |
| `backoffice/views/interviews.py` `get_major_cupt_code_id()` | parser **B**: `== 15` → program only, else program `[:15]`, major `[-1]` |
| `backoffice/views/interviews.py` (~line 254) | `major_cupt_code_map[major.cupt_full_code]` keyed by `get_program_major_code_as_str()`; no default → `KeyError` on blank/unknown code |
| `backoffice/views/projects.py` (~lines 400, 411) | string equality against `get_program_major_code_as_str()` and between two majors |

### Bypasses: read `detail_items_csv[-2:]` instead of the stored field

| Location | Use |
|---|---|
| `backoffice/views/api/__init__.py` (~line 166) | `program_id` / `major_id` for the API payload |
| `scripts/export_project_applicants_tcas.py`, `scripts/export_project_applicants_tcas_old64.py` | same |
| `scripts/export_major_criterias_as_json.py` `get_program_major_code_from_major()` | same |

These break on the missing-major-column case above.

### Scripts using `get_full_major_cupt_code()`

Compared against CUPT-provided major numbers (possibly legacy format):

- `scripts/export_project_applicants.py`
- `scripts/import_clearing_results_all_projects.py`
- `scripts/validate_results.py` — only caller passing `project`, i.e. the
  only one exercising the fallback's parameters.

### Scripts using `cupt_full_code`

| Script | Use |
|---|---|
| `update_major_additional_notice_and_form.py` | parser A |
| `update_major_slots.py` | filter by CSV value |
| `import_tcas3_applicants67.py` | builds `program + '0' + major` itself, treating `'0'` (not `''`) as "no major" |
| `cache_api_project_applications.py` | key `project.cupt_code + cupt_full_code` |
| `update_suphan.py` | one-off code rename |
| `update_major_interview_description_caches.py`, `check_interview_acceptance_results.py` | copies of the `projects.py` span-matching logic |
| `update_major_cupt_full_code.py`, `import_major_codes.py`, `import_majors.py` | writers |

Tests: `criteria/tests.py` fixture sets `cupt_full_code=program_code`.

## Duplication to unify

1. **Composition** of the string is hand-rolled in several places:
   `import_majors.py`, `update_major_cupt_full_code.py`,
   `import_tcas3_applicants67.py`, `update_suphan.py`, plus
   `MajorCuptCode.get_program_major_code_as_str()`.
2. **Parsing** has two divergent implementations (A in
   `MajorCuptCode.get_from_full_code`, B in `interviews.get_major_cupt_code_id`).
3. **Program/major ids** are re-read from `detail_items_csv[-2:]` in four
   places instead of from the stored field.
4. **Legacy fallback** `'002'…` in `get_full_major_cupt_code()` is likely
   dead but still reachable from three scripts.
5. **Silent failure**: a wrong/blank `cupt_full_code` makes lookups return
   `None`, so criteria, interview dates and upload-slot sync silently skip
   the major.

## Suggested future plan

Roughly in order; each step is independently shippable.

1. **Single compose/parse pair.** Add module-level helpers (e.g. in
   `criteria/models/major_cupt_code.py`):
   `compose_full_code(program_code, major_code)` and
   `split_full_code(full_code) -> (program_code, major_code)` with one
   agreed rule (program = first 15 chars, major = what follows the `'0'`
   separator). Make `get_program_major_code_as_str()`,
   `get_from_full_code()` and `interviews.get_major_cupt_code_id()` use
   them. Add unit tests for blank, single-letter and missing-column cases.
2. **Model accessors on `Major`.** e.g. `Major.get_cupt_program_major()`
   returning `(program_id, major_id)` from `cupt_full_code`; switch the API
   view and the three export scripts off `detail_items_csv[-2:]`.
3. **Retire the legacy fallback.** Confirm no current data has blank
   `cupt_full_code` (query), then make `get_full_major_cupt_code()` return
   `cupt_full_code` only (or fold callers onto the field) and consider
   dropping `Major.cupt_code` / `cupt_study_type_code`.
4. **Shared span-matching.** Extract the `projects.py` interview-description
   span logic into a function used by the view and both scripts.
5. **Harden lookups.** Give `interviews.py` a default on the code map; add a
   backoffice/validation check listing majors whose `cupt_full_code` doesn't
   resolve to a `MajorCuptCode`.
6. **(Optional) Real FK.** Add `Major.major_cupt_code = FK(MajorCuptCode,
   null=True)` populated at import, or populate `CurriculumMajor.major`, so
   the string becomes a denormalized display value rather than the join key.
   Then decide whether to retire `update_major_cupt_full_code.py` /
   `import_major_codes.py`.
