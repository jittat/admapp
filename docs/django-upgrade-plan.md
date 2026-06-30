# Django 4.1.13 → 6.0.3 Migration Plan

## Summary

The codebase is in reasonably good shape — modern patterns are used throughout. The biggest risks are **third-party package compatibility** and **Python version requirements**. Direct jumping from 4.1 to 6.0 is feasible but should be done in staged version hops to catch deprecation warnings at each step.

---

## Phase 0: Prerequisites

### Python Version

Django 6.0 requires Python 3.12+. Verify current Python version and upgrade if needed:

```bash
python --version
```

If below 3.12, upgrade Python before upgrading Django.

### Staging Environment

All upgrades should be tested in a staging/dev environment with a copy of production data.

---

## Phase 1: Upgrade to Django 4.2 LTS (Low Risk)

Django 4.2 is the LTS bridge between 4.1 and 5.x.

### Required Changes

| File | Change |
|------|--------|
| `requirements.txt` / `Pipfile` | `django==4.2.x` |

### Expected deprecation warnings to appear (fix, do not suppress)

- `USE_L10N = True` in `admapp/settings.py` — deprecated in 4.2, removed in 5.0. **Remove this line.**
- Any remaining `NullBooleanField` references in old migrations are harmless and can stay.

### Verify

```bash
python manage.py check --deploy
python manage.py migrate
```

---

## Phase 2: Upgrade Third-Party Packages (High Priority)

All third-party packages are pinned at early-2024 versions. For Django 6.0 compatibility, every package needs updating. This is the **highest-risk step**.

| Package | Current | Action |
|---------|---------|--------|
| `djangorestframework` | 3.14.0 | Upgrade to latest (3.15+); verify Django 6.0 support |
| `django-crispy-forms` | 2.0 | Upgrade to latest |
| `crispy-bootstrap4` | 2022.1 | Upgrade to latest |
| `django-debug-toolbar` | 4.3.0 | Upgrade to latest (5.x+) |
| `django-extensions` | 3.2.3 | Upgrade to latest |
| `django-filter` | 23.5 | Upgrade to latest |
| `django-mailer` | 2.1 | Upgrade to latest; verify Django 6.0 support |
| `django-ses` | 3.5.2 | Upgrade to latest |
| `Pillow` | 10.2.0 | Upgrade to latest |
| `openpyxl` | 3.1.2 | Upgrade to latest |
| `asgiref` | 3.7.2 | Will be updated by Django automatically |
| `six` | 1.16.0 | **Remove** — not used in this codebase, Python 2 compat only |
| `future` | 0.18.3 | **Remove** — verify no actual usage first |
| `xlrd` | 2.0.1 | Only supports `.xls` (not `.xlsx`); use `openpyxl` instead if xlsx needed |

---

## Phase 3: Upgrade to Django 5.2 LTS

Once packages are compatible, step to 5.2 (the LTS before 6.0).

### Changes required by this step

1. **`USE_L10N`** (removed in 5.0) — already removed in Phase 1.

2. **`CSRF_COOKIE_MASKED`** — check if set in settings; removed in 5.0.

3. **Admin action `short_description`** — In Django 5.0, the `@admin.action(description=...)` decorator is preferred over setting `.short_description` on action functions. Not strictly breaking but raises warnings. Affects `appl/admin.py`, `backoffice/admin.py`, etc.

4. **`ModelAdmin.list_display` with callables** — review admin files for any callable-based `list_display` entries that rely on deprecated patterns.

5. **`ForeignObject` constraints** — verify all migrations with `ForeignKey` pointing to non-unique `to_field` values.

6. **Template engine** — check for `TEMPLATES[0]['OPTIONS']['string_if_invalid']` usage.

### Run with deprecation warnings as errors

```bash
python -W error::DeprecationWarning manage.py check
```

Fix every deprecation warning — they become errors in the next major version.

---

## Phase 4: Upgrade to Django 6.0.3

### Known changes to verify (5.x → 6.0)

1. **Removed features from Django 5.x deprecation cycle** — must have cleared all `RemovedInDjango60Warning` warnings from Phase 3.

2. **`django-debug-toolbar`** — ensure compatibility with Django 6.0; debug toolbar versions have historically lagged major Django releases.

3. **`LocaleMiddleware`** — still in use; verify behavior unchanged with Django 6.0's i18n changes (the app uses Thai/English i18n heavily via `i18n_patterns()`).

4. **Database backend** — if using PostgreSQL, verify psycopg driver version. Django 5.0+ dropped support for psycopg2 < 2.9 and Django 6.0 may require psycopg 3.

5. **ASGI/async** — if any async views are added in the future, check compatibility.

---

## Phase 5: Post-Upgrade Verification

### Systematic testing checklist

- [ ] `python manage.py check --deploy` — zero warnings/errors
- [ ] `python manage.py migrate` — all migrations apply cleanly
- [ ] `python manage.py test` — full test suite passes
- [ ] Admin interface: browse all registered models in Django admin
- [ ] REST API: test all endpoints in `api/urls.py`
- [ ] Forms: test all crispy forms (admission application forms)
- [ ] i18n: test Thai/English language switching
- [ ] File uploads: test any `ImageField`/`FileField` forms (Pillow dependency)
- [ ] Email: test email queuing (django-mailer) and SES backend (django-ses)
- [ ] Excel exports: test all `xlsxwriter`/`openpyxl` based exports
- [ ] Barcode generation: test `python-barcode` integration
- [ ] Debug toolbar: confirm it works (or disable in production config)

---

## Risk Summary

| Risk | Severity | Notes |
|------|----------|-------|
| Third-party package compatibility | **HIGH** | All packages are ~2 years old; some may not support Django 6.0 |
| Python version upgrade | **HIGH** | If currently on Python < 3.12 |
| `USE_L10N` removal | **LOW** | One line to delete |
| Model/URL/View code | **LOW** | Codebase already uses modern patterns |
| Admin action decorators | **LOW** | Style change, not breaking |
| i18n behavior changes | **MEDIUM** | App is heavily localized (Thai); test carefully |

---

## Recommended Approach

1. **Do NOT jump directly** from 4.1 → 6.0 in one step. Use the hop: `4.1 → 4.2 → 5.2 → 6.0`.
2. At each hop, run with `-W error::DeprecationWarning` and fix all warnings before moving to the next version.
3. Upgrade third-party packages in a separate step before or alongside 4.2, confirming each package has explicit Django 6.0 support in its changelog.
4. The `django-mailer` and `django-ses` packages are email-critical — test these carefully at each step.
