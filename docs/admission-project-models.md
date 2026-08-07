# Admission Project Models

Field reference for the core project/round/major models in `appl/models.py`:
`AdmissionProject`, `AdmissionRound`, `AdmissionProjectRound`, and `Major`.
This is a point-in-time reading of `appl/models.py` (with flag behavior
cross-checked against `backoffice/`, `appl/views/`, `criteria/`, and
templates) — verify line numbers against current code.

Many fields carry a Thai `verbose_name` (shown in the Django admin and staff
UI); those are quoted below because they are the clearest statement of
intent. `appl/models.py` and the migrations remain the source of truth.

## How the models relate

```
Campus 1───* Faculty
   │             │
   │ (FK, null)  │ (FK)
   ▼             ▼
AdmissionProject *───────* AdmissionRound
        │   (M2M through AdmissionProjectRound)
        │
        │ 1───* Major (FK admission_project, FK faculty)
        │
        └─ per (project, round) settings live on AdmissionProjectRound
```

- **`AdmissionProject`** — a whole admission program (e.g. a portfolio
  project). Holds project-wide content and **feature flags**.
- **`AdmissionRound`** — a TCAS round (1, 2, 3, …) shared across projects.
- **`AdmissionProjectRound`** — the M2M "through" row; holds everything that
  is **per project *and* round** (open/close times, freezes, what applicants
  can see). This is where most workflow state lives.
- **`Major`** — a selectable major within a project.

Resolve a project's settings for a given round with
`project.get_project_round_for(admission_round)` → `AdmissionProjectRound`
(or `None`).

---

## AdmissionProject

`appl/models.py:107`. A program that applicants apply to. Related
`AdmissionProjectRound` rows carry the per-round workflow state (see below).

### Identity & content

| Field | Type | Meaning |
|---|---|---|
| `title` / `short_title` | Char | Full / short project name. |
| `campus` | FK `Campus` (null) | Owning campus; `SET_NULL` on delete. |
| `descriptions` | Text | "รายละเอียดโครงการ" — full project description. |
| `short_descriptions` | Char | "รายละเอียดโครงการ (สั้น) แสดงในหน้าแรก" — short blurb on the landing page. |
| `applying_confirmation_warning` | Text | "แจ้งยืนยันก่อนสมัคร" — shown as a confirm-before-apply warning. |
| `general_conditions` | Text | Free-text general conditions. |
| `column_descriptions` | Text | Header/column template for the major detail table; parsed by `get_major_description_table_header()` / `..._list_template()` (see `appl/header_utils.py`). Pairs with `Major.detail_items_csv`. |
| `display_rank` | Int | "สำหรับใช้เรียงรายการ" — sort key for listing projects. |
| `cupt_code` | Char | Project code used to build CUPT/TCAS full major codes and to derive project *type* on export. |

### Visibility

| Field | Default | Meaning |
|---|---|---|
| `is_available` | `False` | Public/applicant-visible. `AdmissionRound.get_available_projects()` and much of `main`/`appl` filter on this. |
| `is_visible_in_backoffice` | `False` | Visible to staff in backoffice, and the set the CUPT export iterates over. A project can be backoffice-visible without being publicly available. |
| `is_apply_link_hidden` | `False` | "ซ่อนลิงก์สมัคร" — hide the apply link. |
| `major_detail_visible` | `False` | "แสดงรายละเอียดสาขา" — show per-major detail. |
| `is_major_with_zero_slots_hidden` | `False` | "ซ่อนสาขาที่จำนวนรับเป็นศูนย์" — hide majors with 0 slots. |
| `applicant_details_hidden` | `False` | When true, staff score tables omit applicant personal detail columns (see `applicant_score_table.html`). |

### Application behavior

| Field | Default | Meaning |
|---|---|---|
| `slots` | `0` | "จำนวนรับ" — total project intake (headline number; per-major intake is `Major.slots`). |
| `max_num_selections` | `1` | "จำนวนสาขาที่เลือกได้" — how many majors an applicant may select. |
| `is_auto_select_single_major` | `False` | "มีสาขาเดียวและเลือกสาขานั้นโดยอัตโนมัติ" — single-major project; the major is auto-selected during apply (`appl/views/__init__.py:495`). |
| `has_selections_with_no_ranks` | `False` | Selections are unranked; changes how the score list is ordered/handled (`backoffice/views/projects.py:459`). |
| `is_portfolio_submission_required` | `False` | "มีการส่งแฟ้มสะสมผลงาน" — portfolio upload required. |
| `base_fee` | `0` | "ค่าสมัคร" — base application fee (per-major surcharges live on `Major`). |

### Criteria-authoring feature flags

These gate what staff can edit in the `criteria` app (see
[criteria.md](criteria.md)):

| Field | Default | Meaning |
|---|---|---|
| `is_criteria_edit_allowed` | `True` | "อนุญาตให้ผู้ดูแลโครงการแก้ไขเงื่อนไขการรับ" — allow project admins to edit criteria. Super admins bypass this. |
| `is_custom_score_criteria_allowed` | `True` | Allow free-form score conditions. |
| `is_custom_curriculum_type_allowed` | `False` | Allow editing accepted school-curriculum types (toggles `AdmissionCriteria.accepted_student_curriculum_type_flags`). |
| `is_custom_graduate_year_allowed` | `False` | Allow choosing accepted graduate-year set (toggles `accepted_graduate_year_flags`). |
| `is_custom_add_limit_criteria` | `False` | Show/allow the per-major "add limit" tie-break intake (`CurriculumMajorAdmissionCriteria.add_limit`). |
| `is_custom_interview_date_allowed` | `False` | Allow choosing interview dates. |
| `custom_interview_start_date` / `custom_interview_end_date` | null | Bounds for custom interview dates. |
| `is_additional_admission_form_allowed` | `False` | Allow extra applicant-form questions (`AdmissionCriteria.additional_admission_form_fields_json`). |
| `is_additional_admission_form_edit_allowed` | `True` | Allow editing those extra questions. |
| `is_additional_admission_upload_allowed` | `False` | Allow extra per-criteria upload documents (`AdmissionCriteria.additional_admission_upload_fields_json`); authoring only so far — see [uploaded-documents.md](uploaded-documents.md). |
| `is_additional_admission_late_upload_allowed` | `False` | "อนุญาตให้เอกสารอัพโหลดเพิ่มเติมอัพโหลดหลังกำหนดได้" — adds a per-upload-field "อัพโหลดหลังหมดเขต" checkbox in the criteria editor. Only takes effect when `is_additional_admission_upload_allowed` is also on. |
| `late_upload_date` | null | "วันสุดท้ายที่อนุญาตให้อัพโหลดล่าช้าได้" — cut-off for those late uploads. Shown (via `thaidate`) in the criteria editor's help text when set; not enforced anywhere yet — that belongs to the not-yet-built upload runtime. |
| `is_additional_notice_allowed` | `False` | Allow an extra applicant-facing notice (`AdmissionCriteria.additional_notice`). |

### Export & basic acceptance criteria

| Field | Default | Meaning |
|---|---|---|
| `is_cupt_export_only_major_list` | `True` | "ส่งข้อมูลทปอ.เป็นรายการสาขาเท่านั้น" — on CUPT export, emit only the major list (skip extracting score/condition criteria). See `cuptexport.py`. |
| `cross_majors_acceptance_visible` | `False` | Show cross-major acceptance info in the score table. |
| `admission_student_type` | `1` | `STUDENT_TYPE_CHOICES`: 1 = only current M.6; 2 = M.6 + graduates. |
| `admission_school_type` | `1` | `SCHOOL_TYPE_CHOICES`: 1 = any; 2–6 = restrict to core/international/vocational/non-formal/GED curricula. |

`admission_student_type` / `admission_school_type` are edited via
`backoffice/views/projectoptions.py` and rendered with the generated
`get_admission_student_type_display()` / `get_admission_school_type_display()`.

### Useful methods

- `get_project_round_for(round)` → the `AdmissionProjectRound` (or `None`).
- `is_open()` / `is_deadline_passed()` — aggregate across the project's rounds.
- `get_single_round_number()` — first round's number (for single-round projects).
- `get_majors_as_dict(with_faculty=False)` — `{major.number: Major}`.
- `get_major_description_table_header()` / `get_major_description_list_template()`
  — build the major-detail table from `column_descriptions`.

---

## AdmissionRound

`appl/models.py:50`. A TCAS round, shared by many projects.

| Field | Type | Meaning |
|---|---|---|
| `number` | Int | Round number (1, 2, 3, …). |
| `subround_number` | Int (0) | Sub-round; `0` means none. `__str__` renders "รอบที่ N" or "รอบที่ N.M". |
| `rank` | Int | Ordering key (`Meta.ordering = ['rank']`). |
| `short_descriptions` | Char | "รายละเอียดสั้น ๆ (แสดงในหน้าแรก)". |
| `admission_dates` | Char | "กำหนดการ" — schedule text. |
| `is_available` | Bool (F) | "แสดงเป็นรอบการรับสมัครต่อผู้สมัคร" — show this round to applicants. |
| `is_application_available` | Bool (F) | "ยังแสดงใบสมัครจากรอบนี้ในรอบสมัครอื่น ๆ" — keep this round's applications visible from other rounds. |
| `clearing_house_description` | Text | "ข้อมูลการยืนยันสิทธิ์" — clearing-house (ทปอ.) confirmation info. |
| `acceptance_result_date` | Date | "วันที่ประกาศผลการคัดเลือก" — result-announcement date (used in messages). |
| `clearing_house_dates` / `clearing_house_dates_short` | Char | ทปอ. confirmation dates (long / short forms for messaging). |

Methods: `get_full_number()` ("N" or "N/M"), static `get_available()` (first
`is_available` round or `None`), `get_available_projects()`.

---

## AdmissionProjectRound

`appl/models.py:269`. The M2M through-row for one `(admission_project,
admission_round)` — this is where **per-round workflow state** lives. Most
staff-facing gating (open/close, freezes, what applicants see) is here, not
on `AdmissionProject`. See [interview-call.md](interview-call.md) for how the
interview-call flags drive that workflow.

### Scheduling / open state

| Field | Meaning |
|---|---|
| `admission_dates` | Per-round schedule text. |
| `is_auto_start` | Auto-open at `applying_start_time`. |
| `is_started` | "เปิดรับสมัครแล้ว" — applications opened. |
| `applying_start_time` / `applying_deadline` | Open / close datetimes. |
| `payment_deadline` | "วันชำระค่าสมัครวันสุดท้าย" — last payment date. |

`is_open()` = `is_started and not is_deadline_passed()`;
`is_deadline_passed()` compares `applying_deadline` to now (true if unset).

### Basic-criteria checking

| Field | Meaning |
|---|---|
| `criteria_check_required` | "มีการตรวจเกณฑ์พื้นฐานก่อน" — basic-criteria check required. |
| `multimajor_criteria_check_required` | Same, for multi-major applications. |
| `criteria_check_frozen` | "ปิดการแก้ไขผลการตรวจเกณฑ์พื้นฐาน" — freeze basic-criteria results. |
| `criteria_edit_only_staff_allowed` | Only staff may edit basic-criteria results. |

### What applicants can view

| Field | Meaning |
|---|---|
| `applicant_info_viewable` | "สามารถดูรายละเอียดผู้สมัครได้" — applicant detail viewable. |
| `applicant_score_viewable` | "แสดงคะแนนสำหรับการคัดเลือก" — show calculated selection scores. |

### Interview-call results

| Field | Meaning |
|---|---|
| `only_bulk_interview_acceptance` | "เรียกสัมภาษณ์ตามคะแนนเท่านั้น" — interview calls decided by a single score cutoff (see interview-call.md; `Major.is_forced_individual_interview_call` overrides per major). |
| `accepted_for_interview_result_frozen` | "ปิดการแก้ไขผลการเรียกสัมภาษณ์" — freeze interview-call decisions. |
| `accepted_for_interview_result_shown` | "แสดงผลการเรียกสัมภาษณ์กับผู้สมัคร" — show call results to applicants. |
| `accepted_for_interview_instructions` | Text shown to called applicants. |

### Final acceptance results

| Field | Meaning |
|---|---|
| `accepted_result_frozen` | "ปิดการแก้ไขผลการรับเข้าศึกษา" — freeze final acceptance. |
| `accepted_result_shown` | "แสดงผลการรับเข้าศึกษากับผู้สมัคร" — show acceptance to applicants. |
| `accepted_instructions` | Text shown to accepted applicants. |

---

## Major

`appl/models.py:339`. A selectable major within a project (FK to
`admission_project` and `faculty`). Ordered by `number`.

### Identity & content

| Field | Type | Meaning |
|---|---|---|
| `number` | Int | Per-project major number (the local id used in selections/URLs). |
| `title` | Char | Major name. |
| `faculty` | FK `Faculty` | Owning faculty. |
| `slots` | Int | Intake for this major. |
| `slots_comments` | Text | Free-text notes about slots. |
| `detail_items_csv` | Text | CSV of detail cells rendered against the project's `column_descriptions` template (`get_detail_items()`, `get_detail_items_as_list_display()`). Supports `--info-start--`/`--info-end--` collapsible blocks. |

### Fees

| Field | Meaning |
|---|---|
| `additional_fee_one_time` | "ค่าสมัครเพิ่มเติม (ไม่คิดซ้ำ)" — extra fee charged once. |
| `additional_fee_per_major` | "ค่าสมัครเพิ่มเติม (คิดซ้ำสาขา)" — extra fee charged per selected major. |

(Total fee builds on `AdmissionProject.base_fee` plus these.)

### CUPT / TCAS codes

| Field | Meaning |
|---|---|
| `ku_code` | KU internal major code. |
| `study_type` | Study-type label. |
| `cupt_code` | CUPT major code fragment. |
| `cupt_study_type_code` | CUPT study-type code fragment. |
| `cupt_full_code` | Full CUPT major code; if blank, `get_full_major_cupt_code()` builds it from `'002' + project.cupt_code + faculty.cupt_code + major + study_type`. |

`get_major_cupt_code()` resolves `cupt_full_code` → `MajorCuptCode`, and
`get_admission_criterias()` walks that to the non-deleted `AdmissionCriteria`
rows for this major (the bridge from the applicant side into the `criteria`
app — see [criteria.md](criteria.md)). `get_interview_date()` returns the
first criteria's interview date.

### Interview behavior

| Field | Default | Meaning |
|---|---|---|
| `is_forced_individual_interview_call` | `False` | "ให้เรียกสัมภาษณ์ไม่ตามคะแนน" — force per-applicant interview-call decisions for this major even when the round is bulk (`only_bulk_interview_acceptance`). See interview-call.md. |

---

## Notes / gotchas

- **Two "slots"**: `AdmissionProject.slots` is the headline project intake;
  actual per-major intake is `Major.slots` (and, for criteria/export, the
  `slots` on `CurriculumMajorAdmissionCriteria`). They are not kept in sync
  automatically.
- **Where does a setting live?** Anything that varies by round (open/close,
  freezes, applicant-visible results) is on **`AdmissionProjectRound`**;
  project-wide content and feature flags are on **`AdmissionProject`**. When
  in doubt, resolve via `get_project_round_for(round)`.
- **`is_available` vs `is_visible_in_backoffice`** are independent — staff
  can see and export a project (`is_visible_in_backoffice`) that is not yet
  public (`is_available`).
- Interview-call flags here are the *round-level* switches; the per-applicant
  decision and per-major cutoff records live in `backoffice` — documented in
  [interview-call.md](interview-call.md).
