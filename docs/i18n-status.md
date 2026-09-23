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
Findings, in order of impact:

1. **Hardcoded Thai throughout applicant templates** (main issue).
2. **Stale catalog**: new strings untranslated or marked fuzzy.
3. **`title_trans` not used** on live pages that show DB titles.
4. **Deploy robustness**: relative `LOCALE_PATHS`, and nothing builds the
   `.mo` file.
5. **`<html lang>` hardcoded to `en`** on every page (small; good first
   step).

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
- Language switcher: `appl/templates/appl/base.html` and
  `main/templates/main/index.html` render a TH/EN button pair using
  `{% get_current_language %}` + `{% language 'en' %}{% url ... %}{% endlanguage %}`.
  It always links to the index page in the other language, not to the
  current page. In `appl/base.html` it's inside `{% if applicant %}`, so
  logged-out `appl` pages have no switcher. Backoffice has none (expected;
  staff UI is Thai-only). `main/templates/base.html` hardcodes
  `<html lang="en">` whatever the active language.
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

## 4. Deploy robustness: relative `LOCALE_PATHS`

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

## 5. `<html lang>` hardcoded to `en`

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

## Open questions for the implementation plan

1. Scope: which applicant pages must be English (registration, application
   forms, major selection, uploads, payment, supplements, printouts)? This
   decides how much of the ~760 hardcoded Thai lines to wrap.
2. Seasonal content (deadline announcements, schedules): catalog entries,
   or per-language template includes/blocks?
3. `.mo` handling: add `compilemessages` to the deploy steps, or commit
   `.mo` files (remove them from `.gitignore`)?
4. Who reviews the English text for the fuzzy/new entries, and should the
   switcher stay "go to index" or keep the current page?
5. Production working directory: check it, or fix `LOCALE_PATHS`
   defensively without checking?
