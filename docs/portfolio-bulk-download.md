# Portfolio Bulk Download

**Status: implemented.**
- The build step: settings, the `backoffice.PortfolioZipFile` model,
  `backoffice/portfolio_zips.py` and `scripts/build_portfolio_zips.py`. See
  [Build step](#build-step-implemented).
- The staff download page with presigned links. See
  [Download page](#download-page-implemented).

The rest of this doc records the design and the alternatives that were
considered.

## Problem

Backoffice users want to download all portfolios (`UploadedDocument`s of one
`ProjectUploadedDocument` slot) for one major of an admission project.

- Files are stored locally under `MEDIA_ROOT` (see
  [uploaded-documents.md](uploaded-documents.md)), typically 5–10 MB each.
- A major can have 20, 40, 80, or even ~900 applicants, so a full major can
  be several GB (900 × ~7.5 MB ≈ 7 GB).
- Constraints:
  - **Server disk is tight**, so building big zip files on local disk is risky.
  - **Gunicorn runs with the default 30 s timeout** and a fixed number of sync
    workers (see [deployment.md](deployment.md)). A long download that
    streams through Django can be killed partway and holds a worker.
  - **Some files exist only in the encrypted S3 backup.**
    `download_uploaded_document_response` (`appl/views/upload.py`) falls back
    to downloading and decrypting from S3, in memory, when the local file is
    missing.
  - **Some entries are links, not files.** TCASFolio submissions are
    `document_url`s; some have a mirrored PDF in `local_document_url`.
  - **This is personal data (PDPA).** Access must be checked and logged.

## Chosen design: offline-built zips on a private Space plus presigned links

### Overview

1. **Build script** (`scripts/build_portfolio_zips.py`), run by hand. It
   takes the project, the round, and the `document_key` of the portfolio
   `ProjectUploadedDocument`.
   - For each major in the project, it loads the major's **paid applicants
     ordered by name** (see [Ordering and naming](#ordering-and-naming)) and
     splits them into batches of **100 applicants per zip**.
   - It streams each zip directly into a private DigitalOcean Space using
     **multipart upload**, so no zip is ever written to local disk.
   - Entries are stored without compression (`ZIP_STORED`), since PDFs and
     images don't compress.
   - Files missing locally are taken from the encrypted S3 backup and
     decrypted. Mirrored TCASFolio PDFs are read from the mirror folder.
   - Each zip includes an `index.csv` listing every applicant in the batch
     and what happened to each document.
   - Each zip is recorded as a `PortfolioZipFile` row.

2. **Storage**: a separate private Space just for these zips, e.g.
   `<portfolio-zip-bucket>`, in the same region as the backup.
   - It has a **lifecycle rule that deletes objects after 30 days** (1 month)
     and aborts unfinished multipart uploads after 1 day.
   - Objects are private. No public ACL and no CDN address.

3. **Download**: a backoffice page per major lists its zips (see
   [Download page](#download-page-implemented)).
   - When the user clicks a zip, Django checks the user's permission for
     that project/major and writes a `LogItem`.
   - Django then generates a **presigned GET URL** valid for 15 minutes and
     redirects to it. The browser downloads straight from Spaces, so
     gunicorn and nginx aren't in the path.
   - If a zip has expired or is gone, the page says so.

### Presigned links (background)

A presigned link is a normal HTTPS URL to one private object, with a
signature and expiry added in the query string (`X-Amz-Expires`,
`X-Amz-Signature`, ...).

- It's computed locally from the access key/secret, with no API call.
- Anyone holding the URL can download until it expires. Editing any part of
  the URL breaks the signature.
- A download that has already started finishes even if the link expires
  midway. Resuming after expiry needs a fresh click, which gives a fresh URL.
- Maximum expiry is 7 days (SigV4).

```python
import boto3
from botocore.config import Config

s3 = boto3.client('s3',
    region_name='<region>',                                  # e.g. the backup's region
    endpoint_url='https://<region>.digitaloceanspaces.com',  # origin, not CDN
    aws_access_key_id=settings.S3_PORTFOLIO_ACCESS_KEY,
    aws_secret_access_key=settings.S3_PORTFOLIO_SECRET_KEY,
    config=Config(signature_version='s3v4'))

url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': settings.S3_PORTFOLIO_BUCKET_NAME, 'Key': key},
    ExpiresIn=900)
return HttpResponseRedirect(url)
```

Why presigned links rather than a public bucket with random prefixes:

| | Random prefix (public) | Presigned (private) |
|---|---|---|
| Works if forwarded | forever | only until expiry |
| Permission check | none | every click, in Django |
| Record of who downloaded | no | yes (`LogItem`) |
| Revoking access | delete the object | happens automatically at expiry |

### DigitalOcean Spaces notes

- Supported: presigned URLs, lifecycle expiration rules (e.g. `s3cmd expire`),
  and multipart upload.
- **Per-bucket ("limited") access keys** are available (Read,
  Read/Write/Delete, All). The app should use a Read/Write/Delete key
  limited to the zip Space, separate from the backup key, stored as new
  `S3_PORTFOLIO_*` settings.
  - Limited keys can't change lifecycle rules. Set the rule once with a
    full-access key, `s3cmd`, or the control panel.
  - Keys can only be created in the control panel.
  - Limited keys don't work on buckets that use bucket policies.
- **Misleading errors seen in production:**
  - A wrong access key/secret gave a bare `InvalidArgument` (HTTP 400, no
    message) on every call, not `InvalidAccessKeyId`.
  - `S3_PORTFOLIO_ENDPOINT` must be the region endpoint
    (`https://<region>.digitaloceanspaces.com`), not the bucket's own address
    (`https://<bucket>.<region>.digitaloceanspaces.com`) that the control
    panel shows. Otherwise boto3 puts the bucket name in the path a second
    time.
  - The build script checks the endpoint at startup, and prints the full S3
    error with a key hint for a bare `InvalidArgument`.
- Older community threads report `SignatureDoesNotMatch` on presigned URLs.
  These were mostly about presigned uploads with mismatched headers. Set
  `signature_version='s3v4'` and the correct `region_name` explicitly.
- Recent `boto3` versions add upload checksums by default, which some
  S3-compatible services reject. If uploads fail with checksum errors, set
  `request_checksum_calculation='when_required'` in `Config`. Whether Spaces
  is affected is unverified.
- **Pricing** (checked 2026-10): $5/month includes 250 GiB of storage and
  1 TiB of outbound transfer, shared across buckets. Extra storage is
  $0.02/GiB/month and extra transfer $0.01/GiB. Downloads are well within the
  included transfer. Storage of all majors' zips for a month, plus the
  backup, may pass 250 GiB, but the overage is small.
- **Data location**: there's no Spaces region in Thailand; Singapore is the
  nearest. Unlike the backup, the zips are **unencrypted** copies of
  applicant documents held outside the server for up to a month, so this
  needs sign-off under the data policy. If needed, the zips could be
  password-protected with AES (`pyzipper`), but staff would need 7-Zip or
  similar, since Windows' built-in unzip can't open AES zips.

### Ordering and naming

**Applicants**: the major's **paid** applicants only, ordered **by name as in
the backoffice**. This is the same code as the score-sheet download
(`download_applicants_score_sheet` in `backoffice/views/reports.py`):

- `load_major_applicants_no_cache` (in `backoffice/views/projects.py`),
- then `sorted_by_name` (Thai collation of first name, then last name, then
  national ID),
- keeping only applicants where `has_paid` is true.

`<seq>` is the applicant's position in that order, starting at 1 for the
whole major, so batch 2 starts at `101`. It is zero-padded to 3 digits (4 if a
major has 1000 or more applicants). The order can change between builds
(late payments), so labels show the applicant range by sequence number and
name, not just "batch 2".

**Files in the zip**: flat, with no folder per applicant.

```
001_1234567890123_สมชาย_ใจดี.pdf       first (usually only) file
001_1234567890123_สมชาย_ใจดี_2.pdf     second file, if any
001_1234567890123_สมชาย_ใจดี_3.pdf     ...
index.csv
```

- The name is `<seq>_<national_id>_<first_name>_<last_name>`, with no title
  (prefix). Each part is cleaned by `safe_filename_part()`:
  - Unicode NFC normalization, keeping Thai vowels and tone marks.
  - Remove control and invisible characters (e.g. zero-width spaces, common
    in Thai input) and `\ / : * ? " < > |`.
  - Turn whitespace inside a name into `_`, trim `_`, `.` and spaces from
    the ends, and cap at 80 characters.
  - An empty name becomes `noname`.
- An applicant's documents are ordered by `rank`, then `id`. The first file
  in the zip gets no suffix, and later ones get `_2`, `_3`, ...
- The extension comes from the stored file name, lowercased. Mirrored PDFs
  are always `.pdf`.
- Python `zipfile` sets the UTF-8 flag for the Thai names. Entries written
  from memory get mode 0644, since without it Linux `unzip` creates
  unreadable files.

**`index.csv`** (UTF-8 with a BOM, so Excel shows the Thai names) is the last
entry in every zip. It has one row per document, or one row for an applicant
with nothing:

| Column | |
|---|---|
| `seq`, `national_id`, `first_name`, `last_name` | the applicant |
| `zip_filename` | the file in the zip; blank if the document is not included |
| `original_filename` | the applicant's upload name (or stored basename) |
| `status` | see below |
| `document_url` | the link, for link entries |

| Status | Meaning | In zip |
|---|---|---|
| `local` | uploaded file, read from `MEDIA_ROOT` | yes |
| `backup` | uploaded file missing locally, restored from the encrypted S3 backup | yes |
| `mirror` | link; the mirrored PDF behind `local_document_url`, read from `LOCAL_DOCUMENT_BASE_PATH` | yes |
| `missing` | uploaded file, neither local nor in the backup | no |
| `mirror-missing` | link with `local_document_url`, but the file wasn't found | no |
| `url-only` | link that was never mirrored | no |
| `no-upload` | applicant has nothing in the slot | no |

**Mirrored PDFs**: `fetch_mytcasfolio_pdf.py <base_path> <base_url>` saves a
PDF to `<base_path>/<filename>` and sets `local_document_url =
<base_url>/<filename>`. The settings `LOCAL_DOCUMENT_BASE_PATH` and
`LOCAL_DOCUMENT_BASE_URL` must hold the same two values.
`mirror_local_path()` accepts only a URL directly under the base URL, with no
`/` or `..` in the file name.

**Object key** (major number zero-padded to 3 digits):

```
<project_id>/<round_id>/major-<NNN>/<YYYYmmdd-HHMMSS>/batch-<NN>.zip
```

The build timestamp means a rebuild never overwrites a zip that someone may
be downloading.

**Download file name** (set with `ResponseContentDisposition` on the
presigned link; ASCII only, since Thai in that header is unreliable across
browsers):

```
portfolio_p<project_id>_r<round_id>_major-<NNN>_batch-<NN>_<first seq>-<last seq>.zip
```

## Build step (implemented)

### Settings (`admapp/settings.py`; real values in `settings_local.py`)

```python
S3_PORTFOLIO_BUCKET_NAME = ''
S3_PORTFOLIO_ENDPOINT = ''        # https://<region>.digitaloceanspaces.com
S3_PORTFOLIO_REGION = ''
S3_PORTFOLIO_ACCESS_KEY = ''      # limited key, this bucket only
S3_PORTFOLIO_SECRET_KEY = ''
S3_PORTFOLIO_EXPIRY_DAYS = 30     # only sets expires_at; S3's lifecycle rule deletes
PORTFOLIO_ZIP_BATCH_SIZE = 100
PORTFOLIO_ZIP_LINK_EXPIRES = 900  # seconds a presigned download link stays valid
LOCAL_DOCUMENT_BASE_PATH = ''     # = fetch_mytcasfolio_pdf.py <base_path>
LOCAL_DOCUMENT_BASE_URL = ''      # = fetch_mytcasfolio_pdf.py <base_url>
```

### Model: `backoffice.PortfolioZipFile`

One row per uploaded zip (one batch of one major):

- **Which zip**: `admission_project`, `admission_round`, `major`,
  `project_uploaded_document`, `batch_number`.
- **Where it is**: `bucket_name`, `object_key`, `size`.
- **What's in it**: `first_seq`, `last_seq`, `first_applicant_name`,
  `last_applicant_name`, `applicant_count`, `file_count`, `missing_count`
  (applicants with no file in the zip).
- **When**: `built_at`, `expires_at` (`built_at` + `S3_PORTFOLIO_EXPIRY_DAYS`).

It is unique on (round, major, slot, batch_number) and shown read-only in the
Django admin. There is no separate build record, since each project is built
once and a major's rows are replaced as a whole on `--rebuild`.

### Script: `scripts/build_portfolio_zips.py`

```
cd scripts
python build_portfolio_zips.py [options] <project_id> <round_id> <document_key>

  --major N [N ...]  only these major numbers (default: all majors)
  --batch-size N     applicants per zip (default PORTFOLIO_ZIP_BATCH_SIZE)
  --dry-run          print batches and planned file names; no S3, no DB writes
  --rebuild          build majors that already have zips again
```

- **Finding the slot**: the `ProjectUploadedDocument` with `document_key`
  that is attached to the project or is a common slot. It must be exactly
  one, otherwise the script exits.
- **Built majors are skipped**: a major that already has rows is skipped, so
  re-running after a failure continues with the remaining majors.
- **All-or-nothing per major**: rows are created only after every batch of
  the major has uploaded.
  - On an error, the failing upload is aborted and that major's earlier
    uploads are deleted. Existing rows are kept, and the script continues
    with the next major and exits with status 1 at the end.
- **`--rebuild`**: swaps a major's rows in one transaction, then deletes the
  old objects.
- **Dry run**: shows a file missing locally as `backup` without fetching it,
  so a file that's in neither place shows up only in a real build.
- **Report**: counts by status for each major, then a list of every document
  that didn't make it into the zips.

Code is in `backoffice/portfolio_zips.py`:
- Naming: `safe_filename_part`, `applicant_file_base`.
- Finding files: `resolve_document`, `mirror_local_path`.
- Writing: `write_batch_zip` writes a zip into any object that has `write()`.
- `S3MultipartWriter` is a write-only object that sends a 16 MB part each
  time its buffer fills.
  - It has no `tell`/`seek`, so `zipfile` uses its streaming mode.
  - Memory use is about 16 MB plus one decrypted backup file.
- `build_major_zips` builds and records one major.
- `get_portfolio_s3_client()` sets s3v4 and checksums "when required", and
  can be reused by the download view.

Tests are in `backoffice/test_portfolio_zips.py` (fake S3 client, SQLite).

### One-time setup

1. Create a private Space `<portfolio-zip-bucket>`.
2. Add a lifecycle rule: expire objects after 30 days, and abort unfinished
   multipart uploads after 1 day.
3. Create a limited Read/Write/Delete key for that Space only, and put it and
   the other `S3_PORTFOLIO_*` / `LOCAL_DOCUMENT_*` values in
   `settings_local.py`.
4. Run `python manage.py migrate backoffice`.

### Decisions made

- **Applicants**: paid applicants only, by name as in the backoffice.
- **Content**: one slot per build (`document_key`). Mirrored TCASFolio PDFs
  are included.
- **Names**: first and last name joined by `_`, with no title. Major number
  zero-padded in object keys.
- **Records**: a single model (`PortfolioZipFile`).
- **Upload**: streamed, with no temp file.
- **Trigger**: run by hand, once per project and round.

## Download page (implemented)

### Where staff find it

On the project's major list (`backoffice/projects/index.html`), each major's
"ดาวน์โหลด" menu has "พอร์ตโฟลิโอ (zip)". It shows only when the major has
unexpired zips:
- `projects.index` counts them with `load_major_portfolio_zip_counts`, which
  sets `major.portfolio_zip_count`.
- The menu flag `download-portfolio-zips` (default on) can hide it per
  project/round through `ProjectMenuConfig`.

The menu is inside the `applicant_info_viewable` part of that page.

### URLs and views (`backoffice/views/projects.py`)

```
projects/<project_id>/<round_id>/<major_number>/portfolios/                    projects-portfolio-zips
projects/<project_id>/<round_id>/<major_number>/portfolios/<zip_id>/download/  projects-download-portfolio-zip
```

- **Permission**: both views use `can_user_view_applicants_in_major`, the
  same as the major's other downloads. Without permission, they redirect to
  the backoffice index.
- **`portfolio_zips`** lists the major's `PortfolioZipFile` rows for the round
  (template `backoffice/projects/portfolio_zips.html`, Thai only). Expired
  rows show "หมดอายุ" and have no button.
- **`download_portfolio_zip`** (GET):
  1. Loads the row and checks it belongs to the project, round and major in
     the URL, otherwise 404.
  2. Checks expiry, then `head_object`. An expired or missing zip, or any
     S3 error, re-renders the list with a message. S3 errors are also
     logged to `backoffice.views.projects` with `describe_error`.
  3. Writes `LogItem("Portfolio zip download by <username>: project <p>
     round <r> major <n> batch <b>")` with the request IP.
  4. Redirects (302) to `presigned_download_url()`.
- **Link expiry**: `PORTFOLIO_ZIP_LINK_EXPIRES` (900 s). A download that has
  started finishes after the link expires; resuming needs a new click.
- **Address style**: boto3 signs path-style URLs for a custom endpoint
  (`https://<region>.digitaloceanspaces.com/<bucket>/<key>?X-Amz-...`).

Tests are in `PortfolioZipViewsTestCase` in `backoffice/test_portfolio_zips.py`.

### Open questions

1. **Staleness**: applicants can still upload interview or late documents
   after a build. Is `--rebuild` by hand enough?
2. **Data policy**: sign-off for unencrypted copies held in Spaces
   (Singapore) for up to 30 days, or use AES-encrypted zips.
3. **Opening the zips**: check that Windows Explorer and macOS open the
   streamed zips with Thai names. The zips use data descriptors because they
   are streamed.

## Alternatives considered

### A. Batches of zips streamed on request (no storage)

A per-major page lists batches. Each link streams a zip built on the fly
with `ZIP_STORED` (e.g. `zipstream-ng`, which can compute `Content-Length`
for a progress bar). Nothing is written to disk.

- Batch by **total size** (about 150–250 MB), not a fixed count, so each
  request stays short.
- Pros: always up to date, no new infrastructure, small change.
- Cons: holds a gunicorn worker per download, hits the 30 s timeout unless
  it's raised or nginx buffering is tuned, and a failed download restarts
  from zero. nginx's response buffering can also write temp files to disk
  (up to 1 GB per response by default) unless it's turned off for that URL.
  Files only in S3 are slow to include.
- Still a reasonable complement for **small majors** (under ~30 applicants),
  where it's fast and always current.

### B. nginx `mod_zip`

Django checks permissions and returns a file manifest. The nginx `mod_zip`
module streams the zip from an internal media location.

- Pros: no disk use, workers are freed immediately, no gunicorn timeout, and
  downloads can resume. A whole major in one zip becomes practical.
- Cons: `mod_zip` isn't in standard nginx packages, so it has to be built
  and maintained. Files only in S3 have to be skipped or restored first.

### C. Background build to local disk, served by nginx

A job writes zips to local disk and nginx serves them (`X-Accel-Redirect`),
deleting them after some hours.

- Pros: downloads can resume, no timeouts.
- Cons: uses exactly the disk space we're short on, and needs a job queue and
  cleanup. **Rejected** for the disk reason; the chosen design is this idea
  with Spaces in place of local disk.

### D. No zip: download into a local folder in the browser

A "download all to folder" button uses the browser's folder-access feature
(`showDirectoryPicker`, Chrome/Edge only). JavaScript downloads files one by
one through the existing per-file endpoint and writes them straight into the
chosen folder.

- Pros: no zip, only short requests, can resume by skipping files that are
  already there.
- Cons: Chrome/Edge only. The fallback would be a file list for a download
  manager or `wget`.
- The per-file endpoint currently uses `HttpResponse(doc_file)`, which reads
  the whole file in Django. Switching to `FileResponse` or `X-Accel-Redirect`
  would make this cheaper.

### E. Download less (combines with any option)

Filters: one slot only, only applicants called for interview, or only files
new since the user's last download. Staff review in rounds, so the last one
fits well.

## Common requirements (any option)

- Reuse the backoffice major-level permission checks.
- Log every bulk download as a `LogItem` (who, project, major, batch).
- Add an `index.csv` to each zip, with file statuses (`ok`, `from-backup`,
  `missing`, `url-only`).
- Use a stable applicant order and show applicant ranges by sequence number
  and name.
- Use `ZIP_STORED`, since content is already compressed.

## References

- DigitalOcean Spaces:
  [sharing / presigned URLs](https://docs.digitalocean.com/products/spaces/how-to/set-file-permissions/),
  [lifecycle rules](https://docs.digitalocean.com/products/spaces/how-to/configure-lifecycle-rules/),
  [API / key permissions](https://docs.digitalocean.com/reference/api/spaces/),
  [limits](https://docs.digitalocean.com/products/spaces/details/limits/),
  [S3 compatibility](https://docs.digitalocean.com/products/spaces/reference/s3-compatibility/),
  [pricing](https://docs.digitalocean.com/products/spaces/details/pricing/).
- In this repo: [uploaded-documents.md](uploaded-documents.md) (storage path,
  S3 encrypted backup, `download_uploaded_document_response`),
  [deployment.md](deployment.md) (gunicorn timeout/workers, nginx).
