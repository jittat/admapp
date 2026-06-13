# Applicant show page (`backoffice` applicant info)

Point-in-time analysis of the staff-facing applicant detail page — the page
that shows a single applicant's profile, applications, payments, and admin
tools. Verify against current code before relying on details here.

## URLs

Defined in `backoffice/urls.py`:

- `applicants/<national_id>/` → `views.show`, name `show-applicant`
  (regex `^applicants/([0-9a-zA-Z\d]\d+)/$`)
- `applicants/<national_id>/<project_id>/` → `views.show`, name
  `show-applicant-in-project` (regex `^applicants/(\d+)/([0-9a-zA-Z]\d*)/$`)

Related actions that redirect back to `show-applicant`:

- `applicants/<national_id>/cancel-confirmation/` →
  `views.cancel_confirmed_application` (`update-applicant-cancel-confirmed-app`)
- `new_password/<national_id>/` → `views.new_password` (`new-password`)
- `update/<national_id>/` → `views.update_applicant` (`update-applicant`)
- `login/<national_id>/<login_key>/` → `views.login_as_applicant`
  (`login-as-applicant`, super-admin only)

## View

`backoffice/views/__init__.py` → `show(request, national_id, project_id=None)`
(decorated with `@user_login_required`).

Flow:

1. Resolve `project` from `project_id` if given (else `None`).
2. **Access control:**
   - Super admins: unrestricted.
   - Non-super-admins: `project_id` is required (else `HttpResponseForbidden`);
     the user must pass `can_user_view_project(user, project)`
     (from `.permissions`), else redirect to `backoffice:index`.
3. Load `applicant` (`get_object_or_404(Applicant, national_id=...)`) and
   `all_applications = applicant.get_all_active_applications()`.
4. Filter to `applications`: super admins see all; others see only apps whose
   `admission_project_id == int(project_id)`.
5. Further non-super-admin gates:
   - if no matching applications → redirect to index;
   - if not `is_admission_admin`, the user must have applied to the user's own
     faculty (`a.has_applied_to_faculty(user.profile.faculty)`) on at least one
     app, else redirect to index.
6. Gather profile data: `education = applicant.get_educational_profile()`,
   `personal = applicant.get_personal_profile()`,
   `payments = Payment.objects.filter(applicant=applicant)`.
7. For each app, attach `supplement_configs` via
   `load_supplement_configs_with_instance(applicant, app.admission_project)` and
   render each instance with `render_supplement_for_backoffice` (sets `c.html`).
8. Super-admin-only extras: `logs = applicant.logitem_set.all()` and an
   editable `ApplicantForm` (email/prefix/first_name/last_name). Others get
   `logs = []`, `applicant_form = None`.
9. `cupt_confirmations = CuptConfirmation.objects.filter(applicant=applicant)`.
10. `notice = request.session.pop('notice', None)` (one-shot flash message).

Context passed to template: `applicant`, `education`, `personal`,
`applicant_form`, `applications`, `payments`, `cupt_confirmations`, `logs`,
`notice`.

### `ApplicantForm`

Defined at the top of `backoffice/views/__init__.py`: `email`, `prefix`
(choices นาย/นางสาว/นาง), `first_name`, `last_name`. Used by
`update_applicant`, which (when email changes) resets the password and emails
the applicant, and logs a `LogItem`.

## Template

`backoffice/templates/backoffice/show.html` — extends
`backoffice/base.html`. Renders a heading (`national_id` + full name), an
optional success `notice` alert, then a single Bootstrap table whose body is
composed of conditional include partials (in
`backoffice/templates/backoffice/include/`):

- `applicant_info_rows.html` — always.
- `applicant_payment_rows.html` — if `payments`.
- `applicant_applications_rows.html` — if `applications`. Shows per app: round,
  project (+ verification number for super admins), a confirmation badge with a
  super-admin "cancel confirmation" button/form, rendered supplements, and the
  selected majors list (`app.major_selection.get_majors`).
- `applicant_admin_rows.html` — if `user.is_super_admin`.

> Note: `*.html~` editor-backup copies exist alongside the real partials; ignore
> them.

## Confirmed-application cancel flow

An applicant's `confirmed_application_id` (on `Applicant`) points at the
`ProjectApplication` they confirmed (ยืนยันสิทธิ์). It is surfaced in
`applicant_applications_rows.html`: the app whose `id ==
applicant.confirmed_application_id` gets a "ยืนยัน" badge, and super admins can
cancel it.

Cancel UX (super-admin only, all in `applicant_applications_rows.html`):

- Click the "ยืนยัน" badge (`#app_cancel_toggle_id`) → reveals the "ยกเลิก"
  button (`#app_cancel_id`).
- Click "ยกเลิก" → hides the button and `slideDown()`s the cancel form
  (`#app_cancel_form_id`), which contains a `confirm_digits` text input asking
  for the **last 4 digits of the applicant's national id**. (Previously this
  used a native `confirm()` dialog.)
- On submit, JS compares the input to `{{ applicant.national_id|slice:'-4:' }}`
  and blocks with an inline error (`#app_cancel_error_id`) on mismatch.

Server side: `cancel_confirmed_application` (`backoffice/views/__init__.py`,
POST + super-admin only) **re-verifies** `confirm_digits` against
`applicant.national_id[-4:]` before clearing the confirmation — on mismatch it
sets a failure `notice` and redirects without changing anything. On success it
logs a `LogItem`, clears `confirmed_application_id`, and sets a success
`notice`. Only one app per page can match, so the fixed element ids are safe.

> Note: `show.html` always renders `notice` as a green `alert-success`, so even
> failure notices appear green (matching `update_applicant`'s error path).

## Extension points

To add a feature to this page, the established pattern is:

1. Compute/attach the new data in `show()` and add it to the render context
   (annotate each `app` object if the data is per-application, mirroring
   `supplement_configs`).
2. Add a new `applicant_*_rows.html` partial and `{% include %}` it from
   `show.html`, gated by the appropriate condition/permission (`payments`,
   `applications`, `user.is_super_admin`, etc.).
3. For interactive actions, add a URL + view that redirects back to
   `show-applicant` and uses `request.session['notice']` for feedback plus a
   `LogItem` for the audit trail (see `new_password` / `cancel_confirmed_application`).
