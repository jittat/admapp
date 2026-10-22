# Portfolio Bulk Download (design notes)

**Status: planned, not implemented.** This records the chosen design and the
alternatives that were considered, so we can pick it up again when we build
the feature. Discuss and confirm the open questions before implementing.

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

1. **Build script** (management command or `scripts/` script), run offline.
   It takes the project, the round, and the `document_key` of the portfolio
   `ProjectUploadedDocument`.
   - For each major in the project, it loads that major's applicants in UI
     order (see [Ordering](#ordering-and-naming)) and splits them into
     batches of **100 applicants per zip**.
   - It writes each zip directly to a private DigitalOcean Spaces bucket
     using **multipart upload**, so no full zip ever sits on local disk. If a
     temp file is used instead, it must be a single batch, deleted right
     after upload.
   - Entries are stored without compression (`ZIP_STORED`), since PDFs and
     images don't compress.
   - Files missing locally are taken from the encrypted S3 backup and
     decrypted. This is offline, so it can be slow without causing problems.
   - Each zip includes an `index.csv` that lists every applicant in the
     batch, the file(s), and a status: `ok`, `from-backup`, `missing`,
     `url-only`.
   - The script records what it built, e.g. in a small model or a JSON
     manifest per major: object key, batch number, applicant range, size,
     file count, build time.

2. **Storage**: a separate private Space just for these zips, e.g.
   `<portfolio-zip-bucket>`, in the same region as the backup.
   - It has a **lifecycle rule that deletes objects after 30 days** (1 month)
     and aborts unfinished multipart uploads after 1 day.
   - Objects are private. No public ACL and no CDN address.

3. **Download**: a backoffice page per major lists its zips, e.g.
   "Batch 1: applicants 1–100 (712 MB, built 2026-10-22 09:00)".
   - When the user clicks a batch, Django checks the user's permission for
     that project/major (reuse the existing major-level checks used by the
     score/applicant pages) and writes a `LogItem`.
   - Django then generates a **presigned GET URL** (expiring after about
     15–30 minutes) and redirects to it. The browser downloads straight from
     Spaces, so gunicorn and nginx aren't in the path.
   - If a zip has expired or was never built, the page says so.

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
    aws_access_key_id=settings.PORTFOLIO_ZIP_S3_ACCESS_KEY,
    aws_secret_access_key=settings.PORTFOLIO_ZIP_S3_SECRET_KEY,
    config=Config(signature_version='s3v4'))

url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': settings.PORTFOLIO_ZIP_S3_BUCKET_NAME, 'Key': key},
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
  `PORTFOLIO_ZIP_S3_*` settings.
  - Limited keys can't change lifecycle rules. Set the rule once with a
    full-access key, `s3cmd`, or the control panel.
  - Keys can only be created in the control panel.
  - Limited keys don't work on buckets that use bucket policies.
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

Applicants inside a major should be **ordered as in the UI**. The backoffice
uses two orders:

- **Major applicant list** (`load_major_applicants` → `sorted_applicants` in
  `backoffice/views/projects.py`): paid first, then Thai-collated first
  name, last name, and national ID.
- **Score page** (`show_scores` → `sort_applicants_by_calculated_scores`):
  calculated score, highest first.

The default plan is the **major applicant list order**; confirm this (open
question 1).

Batch boundaries depend on this order, and it can change between builds
(e.g. payment status changes, late applicants), so applicant N can move to
another batch after a rebuild. The page and `index.csv` should therefore show
the applicant range by **sequence number and name**, not just "batch 2".

**File names are still being worked out.** Current direction:

- **Flat zip with no per-applicant folders.** Each applicant normally has
  exactly one file, named from the applicant, not from the uploaded file name:

  ```
  <seq>_<national_id>_<fullname>.<ext>       first (usually only) file
  <seq>_<national_id>_<fullname>_2.<ext>     second file, if any
  <seq>_<national_id>_<fullname>_3.<ext>     ...
  index.csv
  ```

  Example: `001_1234567890123_สมชาย ใจดี.pdf`, `001_1234567890123_สมชาย ใจดี_2.pdf`.
- `<seq>` is the applicant's position in the major order, zero-padded
  (`001`, `002`, ...), so files sort like the UI. It stays the same numbering
  across all batches of a major (batch 2 starts at `101`).
- `<ext>` comes from the stored file (usually `pdf`).
- If an applicant has several files (e.g. a multi-file slot), order them by
  `rank`, then `id`, so the result is deterministic. The first file gets no
  suffix, and later ones get `_2`, `_3`, ...
- The original upload name isn't in the zip file name. Keep it in
  `index.csv` (`original_filename`, falling back to the stored basename).

Still to decide:
- The exact `<fullname>` format: with or without a title (prefix), a space or
  `_` between first and last name, and Thai or English name.
- Removing characters that are invalid in Windows/macOS file names (`/ \ : *
  ? " < > |`), and trimming whitespace.
- Should the first file be `_1` when an applicant has several, for
  consistency? Current choice: no suffix on the first file.
- Names are Thai. Python `zipfile` sets the UTF-8 flag automatically for
  non-ASCII names; check that Windows Explorer and macOS open them correctly.

Other names (proposed):

```
<object key>  <project-id>/<round-id>/major-<number>/<build-timestamp>/batch-<NN>.zip
<zip file>    <project short title>_major-<number>_batch-<NN>.zip   (Content-Disposition)
```

The download filename can be set with `ResponseContentDisposition` in the
presigned URL params (check that Spaces honours it).

### Settings to add

```
PORTFOLIO_ZIP_S3_BUCKET_NAME
PORTFOLIO_ZIP_S3_ENDPOINT
PORTFOLIO_ZIP_S3_REGION
PORTFOLIO_ZIP_S3_ACCESS_KEY
PORTFOLIO_ZIP_S3_SECRET_KEY
PORTFOLIO_ZIP_BATCH_SIZE = 100
PORTFOLIO_ZIP_LINK_EXPIRES = 900   # seconds
```

### One-time setup

1. Create a private Space `<portfolio-zip-bucket>`.
2. Add a lifecycle rule: expire objects after 30 days, and abort unfinished
   multipart uploads after 1 day.
3. Create a limited Read/Write/Delete key for that Space only, and put it in
   the local settings.

### Open questions

1. **Order**: the major applicant list order or the score order? Which
   applicants are included: all applicants, only those who paid, or only
   those called for interview?
2. **Content**: only the portfolio slot, or optionally several slots (e.g.
   a list of `document_key`s)? Include TCASFolio links that have a mirrored
   PDF (`local_document_url`)?
3. **Staleness**: applicants can still upload interview or late documents
   after a build. Rebuild nightly while the round is open, or have staff
   request a rebuild? Offer a "changes since last build" zip?
4. **Trigger**: only run by hand or cron, or should staff be able to request
   a build ("prepare download") that cron picks up?
5. **Manifest**: store build records in a model (for the page and audit) or
   in a JSON manifest object in the Space?
6. **Data policy**: sign-off for unencrypted copies held in Spaces
   (Singapore) for up to 30 days, or use AES-encrypted zips.
7. **Permission**: anyone who can view the major's scores, or a narrower
   permission?

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
