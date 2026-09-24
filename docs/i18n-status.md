# i18n status (English version)

Point-in-time investigation (2026-09-23, Django 5.2) into why the English
version, set up in late 2017/early 2018, no longer works. Read before working
on this area, but verify against current code.

## Summary

The i18n plumbing still works: from the repo root, `/en/` renders with
`Content-Language: en` and translated strings ("Welcome to Kasetsart").
What the user sees as "English doesn't work" is mostly **coverage**: most
applicant-facing text was added after 2018 as hardcoded Thai and never went
through `{% trans %}`, and the catalog hasn't been maintained since Feb 2018.
Findings, in order of impact (the agreed implementation plan is at the end):

1. **Hardcoded Thai throughout applicant templates** (main issue).
2. **Stale catalog**: new strings untranslated or marked fuzzy.
3. **`title_trans` not used** on live pages that show DB titles.
4. **Deploy robustness**: relative `LOCALE_PATHS`, and nothing builds the
   `.mo` file (fixed).
5. **`<html lang>` hardcoded to `en`** on every page (fixed).

## How it's wired

- `LANGUAGE_CODE` (`admapp/settings.py`) defaults to `'th'`, overridable via
  the `ADMAPP_LANGUAGE_CODE` env var. `manage.py` sets
  `ADMAPP_LANGUAGE_CODE=en` for every management command except
  `runserver`/`testserver`/`test`, so only management-command output is
  forced to English; the served site stays Thai by default.
- `LANGUAGES = [('th', _('Thai')), ('en', _('English'))]`;
  `django.middleware.locale.LocaleMiddleware` is installed right after
  `SessionMiddleware` (correct order).
- URLs are wrapped in `i18n_patterns(...)` in `admapp/urls.py` with
  `prefix_default_language=False`: Thai (default) URLs have no prefix,
  English URLs live under `/en/...`.
- Language switcher (updated in phase 0, `3eaa4e4`): a TH/EN button pair in
  `main/templates/main/include/language_switcher.html`, linking to the
  current page (with query string) in the other language via the
  `{% translated_url 'en' %}` tag in `appl/templatetags/appl_tags.py`
  (wraps Django's `translate_url`). It's included in the navbar of
  `appl/templates/appl/base.html` (only when an applicant is logged in, so
  also on the supplement forms, which extend it) and of
  `regis/templates/regis/base.html` (all `regis` pages). The landing page
  (`main/templates/main/index.html`) keeps its own larger "Apply in
  English" button pair, using the same tag. Pages extending
  `main/templates/base.html` directly have no switcher. Backoffice has none
  (expected; staff UI is Thai-only). Before phase 0 the switcher always
  linked to the index page and didn't exist on `regis` pages.
- Translatable strings: templates use `{% load i18n %}` + `{% trans %}` /
  `{% blocktrans %}`. These tags still work under Django 5.2 (registered
  aliases of `translate`/`blocktranslate`).
- Thai is the **source language**: msgids are Thai, and only an `en` catalog
  exists (`locale/en/LC_MESSAGES/django.po`); there is no `locale/th`.
- DB-stored content (campus/faculty/major/round/project titles) is
  translated at read time: some models in `appl/models.py` expose
  `title_trans`, which returns `_(self.title)` (`AdmissionRound` uses
  `_(str(self))`). `appl/db_messages/model_messages.py` is **never
  imported**; it only holds those DB strings as literal `gettext_lazy` calls
  so `makemessages` puts them in the catalog.

## 1. Hardcoded Thai in templates (main issue)

26 of 209 templates load `i18n`, all in applicant-facing apps (`appl`,
`main`, `regis`), but even those are only partly wrapped. A rough count of
lines containing Thai characters that are **not** on a trans tag (excluding
`~` backup files):

| Templates | Files containing Thai | Thai lines outside trans tags |
|---|---|---|
| `appl/templates` | 53 | ~683 |
| `supplements/templates` | 19 | ~57 |
| `regis/templates` | 4 | ~20 |
| `main/templates` | 2 | ~3 |

Example: on `/en/` the heading is translated, but the whole schedule
announcement (from `appl/include/deadline_announcement_hook.html`,
included by `main/index.html`) stays Thai. This is the bulk of the work.
Some of this text is seasonal (dates, announcements) and may be better
handled per-language than as catalog entries.

`backoffice`, `criteria`, `qrconfirmations`, and `api` templates have no
i18n; that's consistent with staff UI staying Thai-only. `supplements` is
applicant-facing, so it's a gap if English applicants use it.

## 2. Stale catalog

- `locale/en/LC_MESSAGES/django.po` is git-tracked; last touched
  2018-02-06 (16 commits, all Nov 2017 – Feb 2018), about 8 years ago.
- Running `makemessages -l en` against current code (with source locations
  kept) gives 242 entries (was 223). About 23 are marked `#, fuzzy`, where
  gettext guessed a translation from a similar old string. The rest of the
  new entries are untranslated. Only 2 old entries become obsolete (`#~`).
  Examples of new strings: the "application complete" notice, the
  document-upload/TCASFolio validation messages, payment and footer contact
  text.
- `compilemessages` **skips fuzzy entries**, so they show in Thai until
  someone reviews them and removes the fuzzy flag.
- `*.mo` is gitignored, and no script, Dockerfile, or README/INSTALL step
  runs `compilemessages`. The local `django.mo` (compiled 2018-02-05) is
  already older than the committed `.po`: the last "fixed translation"
  commit (`be accepted` → `been accepted`) was never compiled.
- Minor: the catalog translates the language-name labels backwards
  (`"Thai"` → `"ไทย"`, `"English"` → `"อังกฤษ"`) in the `en` locale. It's
  harmless today because the switcher uses hardcoded TH/EN labels.

## 3. `title_trans` not used on live pages

Only 6 templates use `.title_trans`: `major_selection.html`,
`include/major_selection_item.html`, `include/selected_major_details.html`,
`include/active_application.html`, `include/project_list.html`,
`include/project_accepted_for_interview_result.html`.

Other live templates use `.title` (or `{{ major.faculty }}`,
`.faculty.campus.title`) directly, so they never translate whatever the
catalog holds:

- `appl/templates/appl/major_multiple_selection.html`, which is live
  (`appl/views/major_selection.py:97` renders it for multi-major projects).
  It uses `major.title` / `f.title` untranslated, including inside an
  inline JS string.
- `appl/include/project_accepted_result.html` (`major.title`,
  `major.faculty`, `campus.title`).
- `appl/print/*.html` printouts (`m.title`, `row.title`, `province.title`).
  These may be meant to stay Thai; that's a product decision.

`{{ major.faculty }}` goes through `__str__`, which returns the raw title,
so it isn't translated either.

## 4. Deploy robustness: relative `LOCALE_PATHS` (fixed)

Fixed in `b0e50fe`: `LOCALE_PATHS` now uses `BASE_DIR`, `locale/**/*.mo` is
committed (exception in `.gitignore`), and `main/tests.py` checks both.
After editing `django.po`, run `compilemessages` and commit the `.mo`.
The original finding follows.

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
...
LOCALE_PATHS = [
    'locale',
]
```

Other path settings (`MEDIA_ROOT`, the sqlite `NAME`) use
`os.path.join(BASE_DIR, ...)`, but `LOCALE_PATHS` is a bare relative
path, so it's resolved against the **process's current working directory**.
Verified: with `DJANGO_SETTINGS_MODULE`/`PYTHONPATH` set correctly,
`gettext('วิทยาเขตบางเขน')` returns `'Bangkhen Campus'` when the cwd is the
repo root, and the untranslated Thai string when the cwd is `/tmp`. Django
gives no error or warning.

Dev (`runserver` from the repo root) works. Nothing in the repo shows the
production process's working directory, so it's not established that this
breaks production. It's a latent bug worth fixing either way
(`os.path.join(BASE_DIR, 'locale')`).

## 5. `<html lang>` hardcoded to `en` (fixed)

Fixed: the two base templates now use the active language, and the
Thai-only printouts use `lang="th"`. The original finding follows.

Every standalone page template declares `<html lang="en">` whatever
language it's rendered in:

- `main/templates/base.html` (the base for almost all applicant pages)
- `appl/templates/payment_base.html`
- `appl/templates/appl/print/*.html` (`ap`, `common`, `culture`, `el`,
  `gensport`, `inter`, `kus`, `natsport`)

So Thai pages are marked as English. That's wrong for screen readers
(Thai text read with English pronunciation), search engines, and browser
features that depend on page language. The fix is
`{% load i18n %}{% get_current_language as LANGUAGE_CODE %}` +
`<html lang="{{ LANGUAGE_CODE }}">`. The printouts may simply use
`lang="th"` if they're meant to stay Thai (see the product decision in
§3). This is independent of the other findings and a good first step.

## Client-side translation (considered, rejected)

Client-side machine translation isn't a viable replacement for the
catalog. Google's Website Translator widget (`translate_a/element.js`) is
reported to lose support on 2026-10-01. Chrome's on-device Translator API
is desktop-Chrome only, and its Thai support is undocumented. Paid
proxies or the Cloud Translation API on live pages would send applicant
personal data to a third party (a PDPA concern) and publish unreviewed
translations of deadlines, fees, and eligibility rules. Machine
translation may still be useful offline, to draft `.po` entries for human
review.

## Implementation plan

Work happens on the `i18n-english` branch. Status: phases 0 and 1 done
(merged to master); phase 2 in progress (2a done).

### Scope

Every page applicants use gets an English version:

- `main/`: landing page.
- `regis/`: register, login, forgotten password.
- `appl/`: dashboard, personal/education forms, apply/cancel, major
  selection, uploads, payment, per-major additional forms, application
  status.
- `supplements/`: applicant forms (`ap`, `cultural`, `gen_sport`,
  `nat_sport`, `med`, `tcas5`).

Out of scope: `backoffice/*` and `supplements/templates/supplements/backoffice/*`
(staff), `qrconfirmations/` (payment-gateway callbacks, no pages), `api/`,
`admin/`. Also out of scope:

- `appl/templates/appl/payments/*`: bank payment forms meant to be
  printed, no longer used. (`appl/include/payment_item.html`, shown on
  the dashboard, is in scope.)
- `criteria/criteria_options.py`: its text is mostly not shown to
  applicants directly.

### Decisions

- **Printouts (`appl/print/*`) stay Thai** for now; they already use
  `lang="th"`. Labels of links to them on English pages are translated.
- **Seasonal announcements** (e.g. `appl/include/deadline_announcement_hook.html`,
  schedules) use separate Thai and English blocks in the template, chosen
  by `{% get_current_language %}`, not catalog entries. Staff edit both
  blocks each season.
- **Result/print hook templates stay Thai for now**:
  `interview_application_print_hook`, `paper_application_print_hook`,
  `project_accepted_for_interview_result_info_hooks`,
  `project_accepted_result_acceptance_prehook` / `_posthook`,
  `special_cancel_hook` (all in `appl/templates/appl/include/`). They hold
  seasonal, round-specific text that the project owner translates when
  needed.
- **DB titles use optional `title_en` fields** (phase 2e) instead of
  catalog lookups; see phase 2.
- **English text:** machine-translated first drafts, reviewed by the
  project owner before merging.
- **Long free text stored in the DB** (project/interview descriptions,
  uploaded-document titles and details, per-major additional form
  questions, major details) is deferred until everything else is done.
  It shows in Thai on English pages until then.
- **Emails** stay Thai for now (phase 5).
- `.mo` files are committed (done in `b0e50fe`): after editing
  `django.po`, run `compilemessages` and commit the `.mo`.

### Phases

Each phase is one or more commits on the branch.

0. **Language switcher** (done, `3eaa4e4`). The switcher keeps the
   current page when switching (Django's `translate_url`) instead of
   always going to the index. It stays where it was (logged-in `appl`
   navbar, which also covers the supplement forms, plus the landing-page
   buttons) and was added to the `regis` pages. Showing it on every page
   was tried and dropped because it moved the navbar layout too much.

Phases 1–3 go app by app. Each app is finished completely before the next,
so it can be checked under `/en/` as a whole. For each app:

- **Templates:** wrap hardcoded Thai in `{% trans %}` / `{% blocktrans %}`
  (`blocktrans trimmed` for multi-line text and text with variables).
  Thai inside inline JavaScript (`alert()` / `confirm()`) uses
  `{% trans ... as x %}{{ x|escapejs }}`. Seasonal announcements get
  Thai/English blocks (see Decisions).
- **Python strings shown to applicants:** form labels, choices, errors,
  validator and session-notice messages. Staff-only `verbose_name`s are
  skipped. Session notices use `gettext` (not the lazy version), since
  lazy strings can't be stored in the session.
- **Titles from the DB:** use `title_trans` wherever applicants see
  major/faculty/campus/project/round titles, and cover
  `{{ major.faculty }}`-style `__str__` output. Keep
  `appl/db_messages/model_messages.py` in sync with the DB values so
  `makemessages` picks them up.
- **Catalog:** `makemessages -l en`, fill the app's new and fuzzy entries
  with machine-translated drafts (the fuzzy guesses are usually unrelated
  strings), review, `compilemessages`, commit the `.mo`.
- **Tests:** add the app's pages to `EnglishPagesTestCase` in
  `main/tests.py`.

1. **`main` + `regis`.** Landing page, register, login, forgotten
   password, registration result/error pages, the deadline announcement
   (Thai/English blocks), and two unwrapped strings in `regis/views.py`.
   Also updated the old phone number in `regis_result.html` to match the
   footer.
2. **`appl`.** Split into steps, one commit each, each reviewed under
   `/en/` before committing. Templates are under
   `appl/templates/appl/` (mostly `include/`). Payments, criteria options,
   printouts and the hook templates are out of scope (see Scope and
   Decisions).
   - **2a. Dashboard and forms** (done). `index.html`, `active_application`,
     `project_list`, `form_instruction`, `forms/education.html`,
     `other_application_rounds`, `project_deadline_announcement`,
     `major_notices`, `project_supplement_link`. Python:
     `appl/views/general_forms.py`, applicant-facing choices and validator
     messages in `appl/models.py` (e.g. phone number; staff-only
     `verbose_name`s skipped), applicant-visible text in
     `appl/views/__init__.py` and `appl/templatetags/appl_tags.py`. A
     language-aware `thaidate` filter (English month names, Gregorian
     year on English pages; unchanged on Thai pages). Fix the backwards
     `"Thai"`/`"English"` language-name catalog entries. Also added a
     `{% localized_admission_year %}` tag (BE on Thai pages, CE on
     English) so the year isn't baked into msgids. Printouts also use
     `thaidate`, so a printout opened from an English page shows an
     English date. The dashboard test ignores `<script>` blocks until
     2c translates `document_upload_js.html` (`TODO(2c)` in
     `main/tests.py`).
   - **2b. Major selection.** `major_selection_item`,
     `major_multiple_selection.html` (Thai inside inline JS strings via
     `escapejs`), `major_additional_form`, `major_form_field_modal`,
     `major_interview_descriptions`, and the strings in
     `appl/views/major_selection.py`.
   - **2c. Uploads and application status.** `document_upload_js`,
     `documents_incomplete`, `old_document_upload_list`, `payment_item`,
     and the TCASFolio/document validation messages.
   - **2d. Results and confirmation.** `project_accepted_result`,
     `project_accepted_for_interview_result`, `interview_description`,
     `cupt_confirmation_*`, and applicant-visible messages in
     `appl/clearing_utils.py` (check which parts reach applicants).
   - **2e. DB titles.** Replaces the `model_messages.py` /
     `_(self.title)` catalog approach (exact-match lookups that break
     silently when titles change, and a 2017 dump covering only ~16
     majors). One migration adds an optional `title_en` field to
     `Campus`, `Faculty`, `Major` and `AdmissionProject`. `title_trans`
     returns `title_en` on English pages when it is set, else `title`.
     `AdmissionRound.title_trans` builds "Round N" / "Round N.M" with
     gettext (no field). Applicant pages switch from `.title` /
     `{{ major.faculty }}` (`__str__`) to `title_trans`. Delete
     `appl/db_messages/model_messages.py` and the title entries in the
     catalog. The English names are imported later by the project owner
     (no import command in this phase); until then titles show in Thai
     on English pages. Done last so template work isn't blocked on the
     migration.

   Each step includes catalog drafts for its strings, `compilemessages`
   + committed `.mo`, and tests in `EnglishPagesTestCase`. Pages that
   include the untranslated hook templates, or that show DB titles, need
   test fixtures that leave hook content out and (after 2e) set
   `title_en`; before 2e, test titles go on the allow-list.
3. **`supplements`.** Applicant supplement forms (templates and
   `supplements/views/forms/*.py`); not `supplements/backoffice/*`.
4. **Long DB text** (deferred): decide the approach (e.g. optional
   `*_en` fields with Thai fallback, which needs migrations and staff UI)
   after phases 0–3.
5. **Emails** (deferred): every email in `admapp/emails.py` is built in
   Thai in Python. Registration and new-password emails are sent during
   the request and could follow the page language; payment, clearing-house
   and major-confirmation emails are sent outside the applicant's request
   and would need a stored language preference (new field + migration).

### Testing

- `main/tests.py`: `LanguageSwitcherTestCase` (switcher links to the same
  page in the other language) and `EnglishPagesTestCase` (pages rendered
  under `/en/` contain no Thai text outside tags, except an allow-list such
  as the "switch to Thai" link). Pages that only appear after a form
  submission are rendered directly with `render_to_string`.
- Manual review of each app under `/en/` by the project owner before the
  phase is committed.
