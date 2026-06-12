# Interview Call Module

This document describes how the "เรียกสัมภาษณ์" (interview call) decision is
computed, displayed, and edited across the score-list page and the
per-applicant page. It's the result of a code-reading session covering
`backoffice/views/projects.py`, the score-table templates, and the
per-applicant toolbar.

## Core concepts

- **`AdmissionProjectRound`** (appl/models.py) holds round/major-independent
  flags for a project+round:
  - `applicant_score_viewable` — whether calculated scores are shown at all.
  - `only_bulk_interview_acceptance` — if true, interview calls are normally
    decided by a single score cutoff for the whole major.
  - `accepted_for_interview_result_frozen` — real DB flag; when true, the
    interview-call decision can no longer be edited from any page.
- **`Major.is_forced_individual_interview_call`** — overrides
  `only_bulk_interview_acceptance` for a specific major, forcing
  per-applicant decisions even if the round is otherwise bulk-based.
- **`individual_call_only`** (computed, not stored):
  ```python
  individual_call_only = (not project_round.only_bulk_interview_acceptance) \
                          or major.is_forced_individual_interview_call
  ```
  True means: this major's interview-call decisions are made one applicant
  at a time (via `AdmissionResult.is_accepted_for_interview`), not via a
  shared score cutoff.
- **`MajorInterviewCallDecision`** (backoffice/models.py) — per
  (major, admission_round) record holding `interview_call_min_score`
  (the score cutoff) and `interview_call_count`. Used only for
  **bulk** majors (`individual_call_only == False`).
- **`AdmissionResult.is_accepted_for_interview`** — per-applicant
  `BooleanField(null=True)`. `None` = no decision yet. Used as an
  **override** for bulk majors and as the **sole source of truth** for
  individual-call majors.
- **`a.is_called_for_interview`** (computed per applicant in
  `update_interview_call_status`, projects.py):
  ```python
  def update_interview_call_status(applicants, decision, is_individual_only=False):
      for a in applicants:
          if not decision:
              a.is_called_for_interview = False
          elif not a.is_interview_callable:
              a.is_called_for_interview = False
          else:
              if not is_individual_only:
                  a.is_called_for_interview = (
                      a.admission_result.calculated_score
                      > decision.interview_call_min_score - MajorInterviewCallDecision.FLOAT_DELTA
                  )
              if a.admission_result.is_accepted_for_interview:
                  a.is_called_for_interview = True
              elif a.admission_result.is_accepted_for_interview == False:
                  a.is_called_for_interview = False
              elif is_individual_only:
                  a.is_called_for_interview = None
  ```
  - Bulk majors: cutoff-based, unless `is_accepted_for_interview` has been
    explicitly set (True/False), which overrides the cutoff for that
    applicant.
  - Individual-call majors: purely driven by `is_accepted_for_interview`
    (`None` while undecided).

## Page 1: Score list (`show_scores` / `show_applicant_scores.html`)

`backoffice/views/projects.py: show_scores(request, project_id, round_id, major_number)`

1. Loads all applicants for the major (`load_major_applicants_no_cache` +
   `load_check_marks_and_results`, or `load_major_applicants` for the
   special TCAS project id 37).
2. If `applicant_score_viewable`:
   - Sorts applicants by `calculated_score`
     (`sort_applicants_by_calculated_scores`).
   - Loads (or fabricates a dummy) `MajorInterviewCallDecision`.
   - Calls `update_interview_call_status(applicants, call_decision, individual_call_only)`.
   - `interview_call_count = len([a for a in applicants if a.is_called_for_interview])`.
3. Computes `individual_call_editable`:
   ```python
   individual_call_editable = individual_call_only and not project_round.accepted_for_interview_result_frozen
   ```
   This must be computed **before** the next step, which overwrites the
   in-memory `project_round.accepted_for_interview_result_frozen`.
4. For display purposes, if `individual_call_only` is true, the view forces
   the *in-memory* `project_round.accepted_for_interview_result_frozen = True`
   regardless of its real DB value — this hides the bulk checkbox UI for
   individual-call majors. `individual_call_editable` preserves the real
   value so the template can still decide whether to show editable controls.
5. Builds `cross_major_scores` / `cross_major_titles` for the cross-major
   conflict UI (applicants who applied to multiple majors).
6. Renders `backoffice/projects/show_applicant_scores.html` →
   `include/score_table/applicant_score_table.html`.

### Score table rendering (`applicant_score_table.html`)

Per applicant row (`<tr data-appid="{{ a.national_id }}">`), in the
`chboxes` cell, when `a.is_interview_callable` and
`accepted_for_interview_result_frozen` (the in-memory, possibly-forced
value):

- **`individual_call_editable` true** → renders inline
  เรียก/ไม่เรียก buttons:
  ```html
  <span class="btn-group btn-group-sm interview-call-individual-buttons"
        data-natid="{{ a.national_id }}" role="group">
    <a class="interview-call-individual-accept ..." data-decision="accepted">...</a>
    <a class="interview-call-individual-reject ..." data-decision="rejected">...</a>
  </span>
  ```
  highlighted green/red/neutral based on `a.is_called_for_interview`
  (True/False/None).
- **otherwise** (truly frozen, or individual_call_only but frozen) →
  static check/x icon only, no editing.
- **else branch** (`accepted_for_interview_result_frozen` false, i.e. a
  bulk major that isn't individually decided) → the original
  `.call-checkboxes` checkbox, driving the score-cutoff mechanism.

Also rendered (TCAS project only, `is_tcas_project`): a badge showing
`tcas_acceptance_round_number` when called, plus
`.interview-call-rejected` / `.interview-call-canceled` markers computed
from `admission_result.is_tcas_confirmed` / `is_tcas_canceled` — these are
rendered once at page load and are **not** refreshed by either AJAX flow
below (known limitation).

### Client-side JS (`applicant_score_table.html`)

Shared helpers:
```js
showSavingNotice()  // #data_load_notice_id -> fa-spinner fa-spin
showSavedNotice()   // #data_load_notice_id -> fa-check, fades after 1.5s
```

**Bulk checkbox flow** (`.call-checkboxes`):
- POST to `projects-interview-call-score-update`
  (`update_interview_call_score`, see below) with `{nationalId, status}`.
- Response is a **plain-text count**. `updateCall(count)` checks the
  first `count` checkboxes in DOM order (which matches server-side score
  order) and unchecks the rest — relies on the bulk decision always being
  "top N by score".
- Updates `isAcceptedForInterview[natid]`, row classes, then
  `updateConflictCounts()`.

**Individual accept/reject flow** (`.interview-call-individual-buttons a`):
- POST to `projects-individual-interview-call-score-update`
  (`update_individual_interview_call_score`, see below) with
  `{nationalId, decision}`.
- Response JSON: `{is_accepted_for_interview, count}`.
- Updates that row's button highlight classes, `isAcceptedForInterview[natid]`,
  row classes, `.interview-count-spans` text (= `count`), then
  `updateConflictCounts()`.

**Cross-major helpers**:
- `updateMajorMarkers()` — marks `.major-markers` (other-major dots) as
  `.accepted` if `minMajorScore[mnum] < score` (cross-major cutoff
  comparison; independent of interview-call edits).
- `updateConflictCounts()` — counts applicants who are both
  `isAcceptedForInterview[appid]` and have an `.accepted` major-marker;
  updates `#conflict_count_span_id` and `.conflict-list`.

## Page 2: Per-applicant page (`show_applicant` / `show_applicant.html`)

`backoffice/views/projects.py: show_applicant(request, project_id, round_id, major_number, rank)`

- `frozen_results.interview = project_round.accepted_for_interview_result_frozen`
  — the **real** DB value (this page loads `project_round` fresh, so it is
  not affected by `show_scores`'s in-memory override).
- `only_bulk_interview_acceptance = project_round.only_bulk_interview_acceptance and not major.is_forced_individual_interview_call`
  — the inverse of `individual_call_only`.
- `is_accepted_for_interview` comes directly from
  `AdmissionResult.is_accepted_for_interview` (may be `None`).

### Toolbar (`applicant_toolbar.html`)

- If `frozen_results.interview` → static read-only `interview_result.html`.
- Else if `not only_bulk_interview_acceptance` (i.e. individual-call major)
  → editable `interview_buttons.html` (เรียก / ไม่เรียก) inside
  `#interview_button_group_id`.
- Else (bulk major) → link back to the score-table page instead.

### Click handler

```js
$('#interview_button_group_id').on('click', '.interview-selection-buttons', function() {
  saveResult(this, baseSetInterviewUrl, '#interview_button_group_id', '#accepted_for_interview_count_id');
});
```
POSTs to `projects-set-call-for-interview` (`set_call_for_interview`),
decision baked into the URL path. Response JSON `{result, html, count}`:
`html` is a re-rendered `interview_buttons.html`, `count` updates
`#accepted_for_interview_count_id`.

## Backend endpoints

All three endpoints below ultimately call the shared helper:

```python
def apply_interview_call_decision(request, project, admission_round, major, applicant, application, decision):
    # get-or-create AdmissionResult for (application, major)
    # admission_result.is_accepted_for_interview = (decision == 'accepted')
    # admission_result.updated_accepted_for_interview_at = now
    # admission_result.save()
    # LogItem.create('Interview decision (major: {major.number} {decision}) by {user}', applicant, request)
    return admission_result
```

### `update_interview_call_score` (bulk cutoff update)
`POST /projects/scores/<project_id>/<round_id>/<major_number>/interview_score/`
body: `{nationalId, status}` (`status` = `'selected'` / `'not-selected'`)

- Guards: `can_user_view_applicants_in_major`, `applicant_score_viewable`,
  **not** `accepted_for_interview_result_frozen` (real DB value).
- Re-loads & re-sorts applicants, recomputes current `call_decision`.
- `selected`: applicant must not already be called; sets
  `interview_call_min_score = applicant.calculated_score`.
- `not-selected`: applicant must currently be called; finds the
  next-highest-scoring still-callable applicant and sets the cutoff to
  *their* score (or `applicant.score + 1` if none) — i.e. always operates
  on a contiguous "top N by score" cutoff.
- Saves `call_decision`, logs, returns plain-text
  `call_decision.interview_call_count`.
- **Does not** touch `AdmissionResult.is_accepted_for_interview` directly
  — it only moves the cutoff. (An applicant with an explicit
  `is_accepted_for_interview` override would still bypass this cutoff per
  `update_interview_call_status`.)

### `set_call_for_interview` (per-applicant page buttons)
`POST /projects/applicants/<project_id>/<round_id>/<national_id>/<major_number>/interview/<decision>/`

- Guards (via `load_applicant_application_and_check_permission`):
  permission + `has_applied_to_major`; then
  **not** `accepted_for_interview_result_frozen`, and
  **not** (`only_bulk_interview_acceptance and not major.is_forced_individual_interview_call`)
  — i.e. only allowed when `individual_call_only` is true.
- Calls `apply_interview_call_decision`.
- Returns JSON `{result: 'OK', html: <interview_buttons.html>, count}`.

### `update_individual_interview_call_score` (new: inline score-page buttons)
`POST /projects/scores/<project_id>/<round_id>/<major_number>/individual_interview_score/`
body: `{nationalId, decision}`

- Guards: same permission/applied checks as above via
  `load_applicant_application_and_check_permission`, plus:
  - **not** `accepted_for_interview_result_frozen` (real DB value).
  - `individual_call_only` must be true (mirrors `set_call_for_interview`'s
    bulk guard — this is the check that prevents bypassing the score-cutoff
    mechanism on bulk majors).
  - existing `AdmissionResult` must exist and `is_interview_callable()`
    must be true (defense in depth; the buttons are only rendered for
    `a.is_interview_callable` rows anyway).
- Calls `apply_interview_call_decision`.
- Returns JSON `{is_accepted_for_interview, count}` (no rendered HTML —
  the score-table JS updates button classes itself).

## Known limitations / things to watch when extending this module

1. **TCAS confirmation/cancellation styling** (`updateInterviewConfirmation`,
   the `3/{{ tcas_acceptance_round_number }}` badge) is computed once at
   page load from `admission_result.is_tcas_confirmed` /
   `is_tcas_canceled`, and is not refreshed by either AJAX flow. If
   individual-call majors ever combine with the TCAS project (id 37), this
   could go stale after an inline accept/reject.
2. **No "revert to undecided"**: once `is_accepted_for_interview` is set
   (True/False), there is no UI path to set it back to `None`. This is true
   both on the per-applicant page and the new inline score-page buttons.
3. **Bulk vs. individual override interaction**: setting
   `AdmissionResult.is_accepted_for_interview` explicitly (via
   `set_call_for_interview` on a `major.is_forced_individual_interview_call`
   major, for example) overrides the score-cutoff for that applicant even
   in `update_interview_call_status`'s bulk branch. Worth keeping in mind
   if bulk and individual flows are ever mixed for the same major.
4. **`updateCall`'s positional-count assumption**: the bulk checkbox flow
   assumes the called applicants are always exactly the first N in
   score-sorted DOM order. This holds because `update_interview_call_score`
   always maintains a contiguous top-N cutoff, but would break if that
   invariant were ever relaxed.
5. **`is_truncated`**: the score table caps display at 1000 applicants
   (`MAX_APPLICANT_SHOWN`); both AJAX flows operate by `national_id` so
   this doesn't affect correctness, but cutoff-based bulk operations only
   "see" the truncated list.
