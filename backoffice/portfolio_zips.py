"""Bulk portfolio zips: build one major's portfolios into zips of
PORTFOLIO_ZIP_BATCH_SIZE applicants each and stream them into the private
S3_PORTFOLIO_BUCKET_NAME bucket. Driven by scripts/build_portfolio_zips.py;
see docs/portfolio-bulk-download.md.

Zip contents are flat:

    001_<national_id>_<first>_<last>.pdf
    001_<national_id>_<first>_<last>_2.pdf   (second file of the same applicant)
    index.csv

Applicants are the major's paid applicants, ordered by name as in the
backoffice (sorted_by_name); seq numbers run across all batches of a major.
"""
import csv
import io
import os
import re
import unicodedata
import zipfile
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from appl.models import ProjectUploadedDocument, UploadedDocument

S3_PART_SIZE = 16 * 1024 * 1024     # S3 needs >= 5 MB for every part but the last

STATUS_LOCAL = 'local'              # uploaded file, read from MEDIA_ROOT
STATUS_BACKUP = 'backup'            # uploaded file, restored from the encrypted S3 backup
STATUS_MISSING = 'missing'          # uploaded file, neither local nor in the backup
STATUS_MIRROR = 'mirror'            # link, mirrored PDF read from LOCAL_DOCUMENT_BASE_PATH
STATUS_MIRROR_MISSING = 'mirror-missing'  # link with local_document_url, file not found
STATUS_URL_ONLY = 'url-only'        # link, never mirrored
STATUS_NO_UPLOAD = 'no-upload'      # applicant has nothing in this slot

INCLUDED_STATUSES = (STATUS_LOCAL, STATUS_BACKUP, STATUS_MIRROR)

INDEX_FILENAME = 'index.csv'
INDEX_COLUMNS = ['seq', 'national_id', 'first_name', 'last_name',
                 'zip_filename', 'original_filename', 'status', 'document_url']

_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')
_WHITESPACE = re.compile(r'\s+')
_EXTENSION_CHARS = re.compile(r'[^a-z0-9]')


# ---------------------------------------------------------------------------
# Names

def safe_filename_part(text, max_length=80):
    """Make text usable inside a file name on Windows/macOS/Linux.

    Keeps Thai letters, vowels and tone marks; drops control and invisible
    characters (zero-width spaces are common in Thai input) and
    \\ / : * ? " < > |; turns runs of whitespace into a single '_'."""
    text = unicodedata.normalize('NFC', text or '')
    text = ''.join(' ' if c.isspace() else c for c in text)
    text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
    text = _INVALID_FILENAME_CHARS.sub('', text)
    text = _WHITESPACE.sub('_', text.strip())
    text = text[:max_length]
    return text.strip(' ._')


def applicant_file_base(seq, applicant, seq_width=3):
    """<seq>_<national_id>_<first>_<last>, without the extension."""
    parts = [str(seq).zfill(seq_width),
             safe_filename_part(applicant.national_id, 20) or 'noid']
    name_parts = [p for p in (safe_filename_part(applicant.first_name),
                              safe_filename_part(applicant.last_name)) if p]
    parts += name_parts or ['noname']
    return '_'.join(parts)


def zip_entry_name(base, number, extension):
    """number is 1 for an applicant's first file (no suffix), 2 for '_2', ..."""
    suffix = '' if number == 1 else f'_{number}'
    return f'{base}{suffix}{extension}'


def file_extension(filename):
    ext = _EXTENSION_CHARS.sub('', os.path.splitext(filename or '')[1].lower())
    return f'.{ext}' if ext else ''


def applicant_display_name(applicant):
    return f'{applicant.first_name} {applicant.last_name}'.strip()


def object_key_for(project, admission_round, major, timestamp, batch_number):
    return (f'{project.id}/{admission_round.id}/major-{major.number:03d}/'
            f'{timestamp}/batch-{batch_number:02d}.zip')


# ---------------------------------------------------------------------------
# Finding the slot, the applicants and their files

def find_project_uploaded_document(project, document_key):
    """The project's slot with this document_key (attached to the project,
    or a common slot). Raises ValueError unless there is exactly one."""
    docs = list(ProjectUploadedDocument.objects
                .filter(document_key=document_key)
                .filter(Q(admission_projects=project) | Q(is_common_document=True))
                .distinct())
    if len(docs) != 1:
        raise ValueError(f'Expected one document slot with key {document_key!r} '
                         f'for project {project.id}, found {len(docs)}')
    return docs[0]


def load_paid_applicants_by_name(project, admission_round, major):
    """The major's paid applicants in the backoffice name order (Thai
    collation of first name, last name, then national id), as in
    download_applicants_score_sheet."""
    from backoffice.views.projects import load_major_applicants_no_cache
    from backoffice.views.reports import sorted_by_name

    applicants = load_major_applicants_no_cache(project, admission_round, major)
    return [a for a in sorted_by_name(applicants) if a.has_paid]


def load_documents_by_applicant(applicants, project_uploaded_document):
    """{applicant_id: [UploadedDocument, ...]} ordered by rank, then id."""
    documents = {}
    ids = [a.id for a in applicants]
    for d in (UploadedDocument.objects
              .filter(project_uploaded_document=project_uploaded_document,
                      applicant_id__in=ids)
              .order_by('applicant_id', 'rank', 'id')):
        documents.setdefault(d.applicant_id, []).append(d)
    return documents


def mirror_local_path(local_document_url):
    """The file behind a local_document_url written by
    fetch_mytcasfolio_pdf.py, or None when it is not under
    LOCAL_DOCUMENT_BASE_URL (or the settings are blank)."""
    base_url = (settings.LOCAL_DOCUMENT_BASE_URL or '').rstrip('/')
    base_path = settings.LOCAL_DOCUMENT_BASE_PATH or ''
    if not base_url or not base_path or not local_document_url:
        return None
    prefix = base_url + '/'
    if not local_document_url.startswith(prefix):
        return None
    filename = local_document_url[len(prefix):]
    if (not filename or '/' in filename or '\\' in filename
            or filename in ('.', '..')):
        return None
    return os.path.join(base_path, filename)


def resolve_document(document):
    """(status, local path or None, extension) before any backup download.
    STATUS_BACKUP here means "not on local disk, try the backup"."""
    if document.uploaded_file:
        name = document.uploaded_file.name
        path = os.path.join(settings.MEDIA_ROOT, name)
        status = STATUS_LOCAL if os.path.isfile(path) else STATUS_BACKUP
        return status, (path if status == STATUS_LOCAL else None), file_extension(name)
    if document.local_document_url:
        path = mirror_local_path(document.local_document_url)
        if path and os.path.isfile(path):
            return STATUS_MIRROR, path, '.pdf'
        return STATUS_MIRROR_MISSING, None, ''
    if document.document_url:
        return STATUS_URL_ONLY, None, ''
    return STATUS_MISSING, None, ''


def original_filename(document):
    if document.uploaded_file:
        return document.original_filename or os.path.basename(document.uploaded_file.name)
    return ''


def fetch_from_backup(document):
    """Decrypted content from the encrypted S3 media backup, or None."""
    from appl.views.upload import download_and_decrypt_file_from_s3
    return download_and_decrypt_file_from_s3(document)


# ---------------------------------------------------------------------------
# Writing a zip

def _zip_info(name, date_time):
    info = zipfile.ZipInfo(name, date_time)
    info.external_attr = 0o644 << 16    # otherwise unzip on Linux makes it unreadable
    return info


def write_batch_zip(fileobj, numbered_applicants, documents_by_applicant,
                    seq_width=3, fetch_backup=fetch_from_backup, built_at=None):
    """Write one batch as a zip (ZIP_STORED) into fileobj, which only needs
    write() and flush(). numbered_applicants is [(seq, applicant), ...].

    Returns {'file_count', 'missing_count', 'status_counts', 'rows'}; rows
    are the index.csv rows. missing_count counts applicants with no file in
    the zip."""
    built_at = built_at or datetime.now()
    date_time = built_at.timetuple()[:6]
    rows = []
    file_count = 0
    missing_count = 0
    status_counts = {}

    def add_row(seq, applicant, zip_filename, document, status):
        status_counts[status] = status_counts.get(status, 0) + 1
        rows.append({
            'seq': seq,
            'national_id': applicant.national_id,
            'first_name': applicant.first_name,
            'last_name': applicant.last_name,
            'zip_filename': zip_filename,
            'original_filename': original_filename(document) if document else '',
            'status': status,
            'document_url': (document.document_url if document else '') or '',
        })

    with zipfile.ZipFile(fileobj, 'w', compression=zipfile.ZIP_STORED,
                         allowZip64=True) as zf:
        for seq, applicant in numbered_applicants:
            base = applicant_file_base(seq, applicant, seq_width)
            documents = documents_by_applicant.get(applicant.id, [])
            if not documents:
                add_row(seq, applicant, '', None, STATUS_NO_UPLOAD)
                missing_count += 1
                continue

            number = 0
            for document in documents:
                status, path, extension = resolve_document(document)
                content = None
                if status == STATUS_BACKUP:
                    content = fetch_backup(document)
                    if content is None:
                        status = STATUS_MISSING

                if status not in INCLUDED_STATUSES:
                    add_row(seq, applicant, '', document, status)
                    continue

                number += 1
                name = zip_entry_name(base, number, extension)
                if path:
                    zf.write(path, arcname=name)
                else:
                    zf.writestr(_zip_info(name, date_time), content)
                file_count += 1
                add_row(seq, applicant, name, document, status)

            if number == 0:
                missing_count += 1

        index = io.StringIO()
        writer = csv.DictWriter(index, fieldnames=INDEX_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        # utf-8-sig so Excel shows the Thai names correctly
        zf.writestr(_zip_info(INDEX_FILENAME, date_time),
                    index.getvalue().encode('utf-8-sig'))

    return {'file_count': file_count,
            'missing_count': missing_count,
            'status_counts': status_counts,
            'rows': rows}


class S3MultipartWriter:
    """A write-only file object that streams into an S3 multipart upload.

    It deliberately has no tell()/seek(): zipfile then writes in its
    streaming mode (data descriptors), so the zip never needs to be on
    local disk. Call complete() after the ZipFile is closed, or abort() on
    failure."""

    def __init__(self, client, bucket, key, part_size=S3_PART_SIZE):
        self.client = client
        self.bucket = bucket
        self.key = key
        self.part_size = part_size
        self.buffer = bytearray()
        self.parts = []
        self.size = 0
        response = client.create_multipart_upload(Bucket=bucket, Key=key,
                                                  ContentType='application/zip')
        self.upload_id = response['UploadId']

    def write(self, data):
        self.buffer += data
        self.size += len(data)
        while len(self.buffer) >= self.part_size:
            self._upload_part(bytes(self.buffer[:self.part_size]))
            del self.buffer[:self.part_size]
        return len(data)

    def flush(self):
        pass

    def _upload_part(self, data):
        number = len(self.parts) + 1
        response = self.client.upload_part(Bucket=self.bucket, Key=self.key,
                                           UploadId=self.upload_id,
                                           PartNumber=number, Body=data)
        self.parts.append({'ETag': response['ETag'], 'PartNumber': number})

    def complete(self):
        if self.buffer or not self.parts:
            self._upload_part(bytes(self.buffer))
            self.buffer = bytearray()
        self.client.complete_multipart_upload(
            Bucket=self.bucket, Key=self.key, UploadId=self.upload_id,
            MultipartUpload={'Parts': self.parts})

    def abort(self):
        self.client.abort_multipart_upload(Bucket=self.bucket, Key=self.key,
                                           UploadId=self.upload_id)


def endpoint_includes_bucket(endpoint, bucket):
    """True when endpoint is the bucket's own address
    (https://<bucket>.<region>.digitaloceanspaces.com) instead of the
    region endpoint; boto3 then puts the bucket name in the path again."""
    from urllib.parse import urlparse

    if not endpoint or not bucket:
        return False
    host = (urlparse(endpoint).hostname or '').lower()
    return host.startswith(bucket.lower() + '.')


def describe_error(e):
    """A readable one-line description of an exception; for S3 errors the
    code, message, HTTP status and request id."""
    response = getattr(e, 'response', None)
    if not isinstance(response, dict) or 'Error' not in response:
        return f'{type(e).__name__}: {e}'

    error = response.get('Error') or {}
    meta = response.get('ResponseMetadata') or {}
    code = error.get('Code') or '?'
    message = error.get('Message')
    parts = [f'S3 error {code}']
    if message:
        parts.append(message)
    if meta.get('HTTPStatusCode'):
        parts.append(f'HTTP {meta["HTTPStatusCode"]}')
    request_id = meta.get('RequestId') or (meta.get('HTTPHeaders') or {}).get('x-amz-request-id')
    if request_id:
        parts.append(f'request id {request_id}')
    operation = getattr(e, 'operation_name', None)
    if operation:
        parts.append(f'in {operation}')
    text = ', '.join(parts)
    if code == 'InvalidArgument' and not message:
        # What Spaces answered for a wrong access key/secret
        text += ('. Check S3_PORTFOLIO_ACCESS_KEY / S3_PORTFOLIO_SECRET_KEY '
                 '(Spaces gives this error for a wrong key) and S3_PORTFOLIO_ENDPOINT.')
    return text


def get_portfolio_s3_client():
    import boto3
    from botocore.config import Config

    config = Config(signature_version='s3v4',
                    # S3-compatible stores may reject boto3's default checksums
                    request_checksum_calculation='when_required',
                    response_checksum_validation='when_required')
    return boto3.client('s3',
                        region_name=settings.S3_PORTFOLIO_REGION or None,
                        endpoint_url=settings.S3_PORTFOLIO_ENDPOINT or None,
                        aws_access_key_id=settings.S3_PORTFOLIO_ACCESS_KEY,
                        aws_secret_access_key=settings.S3_PORTFOLIO_SECRET_KEY,
                        config=config)


# ---------------------------------------------------------------------------
# Building a major

def make_batches(applicants, batch_size):
    """[[(seq, applicant), ...], ...] with seq starting at 1 for the major."""
    numbered = list(enumerate(applicants, start=1))
    return [numbered[i:i + batch_size] for i in range(0, len(numbered), batch_size)]


def seq_width_for(count):
    return max(3, len(str(count)))


def plan_major(applicants, documents_by_applicant, batch_size):
    """Dry-run plan: per batch, [(seq, applicant, [(entry name or '', status)])].
    Files not on local disk are shown as 'backup' (not fetched)."""
    width = seq_width_for(len(applicants))
    plan = []
    for batch in make_batches(applicants, batch_size):
        items = []
        for seq, applicant in batch:
            base = applicant_file_base(seq, applicant, width)
            files = []
            number = 0
            for document in documents_by_applicant.get(applicant.id, []):
                status, _, extension = resolve_document(document)
                if status in INCLUDED_STATUSES:
                    number += 1
                    files.append((zip_entry_name(base, number, extension), status))
                else:
                    files.append(('', status))
            if not files:
                files.append(('', STATUS_NO_UPLOAD))
            items.append((seq, applicant, files))
        plan.append(items)
    return plan


def build_major_zips(project, admission_round, major, project_uploaded_document,
                     client, bucket, batch_size, rebuild=False,
                     applicants=None, fetch_backup=fetch_from_backup,
                     log=print):
    """Build and upload all zips of one major, then record them as
    PortfolioZipFile rows (all-or-nothing per major).

    Returns a summary dict; 'skipped' is True when the major already has
    zips and rebuild is False. On failure, uploads already made for this
    major are deleted and the exception is re-raised; existing rows are
    kept."""
    from backoffice.models import PortfolioZipFile

    existing = PortfolioZipFile.objects.filter(admission_round=admission_round,
                                               major=major,
                                               project_uploaded_document=project_uploaded_document)
    if existing.exists() and not rebuild:
        return {'skipped': True}

    if applicants is None:
        applicants = load_paid_applicants_by_name(project, admission_round, major)
    documents = load_documents_by_applicant(applicants, project_uploaded_document)

    built_at = datetime.now()
    timestamp = built_at.strftime('%Y%m%d-%H%M%S')
    expires_at = built_at + timedelta(days=settings.S3_PORTFOLIO_EXPIRY_DAYS)
    width = seq_width_for(len(applicants))

    summary = {'skipped': False, 'applicant_count': len(applicants),
               'file_count': 0, 'missing_count': 0, 'size': 0,
               'status_counts': {}, 'batches': 0, 'missing_rows': []}
    new_rows = []
    uploaded_keys = []
    try:
        for batch_number, batch in enumerate(make_batches(applicants, batch_size), start=1):
            key = object_key_for(project, admission_round, major, timestamp, batch_number)
            writer = S3MultipartWriter(client, bucket, key)
            try:
                result = write_batch_zip(writer, batch, documents, width,
                                         fetch_backup=fetch_backup, built_at=built_at)
                writer.complete()
            except BaseException:
                try:
                    writer.abort()
                except Exception as e:
                    log(f'  could not abort upload of {key}: {e}')
                raise
            uploaded_keys.append(key)
            log(f'  batch {batch_number}: seq {batch[0][0]}-{batch[-1][0]}, '
                f'{result["file_count"]} files, {writer.size:,} bytes -> {key}')

            new_rows.append(PortfolioZipFile(
                admission_project=project,
                admission_round=admission_round,
                major=major,
                project_uploaded_document=project_uploaded_document,
                batch_number=batch_number,
                bucket_name=bucket,
                object_key=key,
                size=writer.size,
                first_seq=batch[0][0],
                last_seq=batch[-1][0],
                first_applicant_name=applicant_display_name(batch[0][1])[:200],
                last_applicant_name=applicant_display_name(batch[-1][1])[:200],
                applicant_count=len(batch),
                file_count=result['file_count'],
                missing_count=result['missing_count'],
                built_at=built_at,
                expires_at=expires_at))

            summary['batches'] += 1
            summary['file_count'] += result['file_count']
            summary['missing_count'] += result['missing_count']
            summary['size'] += writer.size
            for status, count in result['status_counts'].items():
                summary['status_counts'][status] = summary['status_counts'].get(status, 0) + count
            summary['missing_rows'] += [r for r in result['rows']
                                        if r['status'] not in INCLUDED_STATUSES]

        with transaction.atomic():
            old_rows = list(existing)
            existing.delete()
            PortfolioZipFile.objects.bulk_create(new_rows)
    except BaseException:
        delete_objects(client, bucket, uploaded_keys, log)
        raise

    # Only after the new rows are saved; the lifecycle rule would delete
    # these anyway.
    for row in old_rows:
        delete_objects(client, row.bucket_name, [row.object_key], log)

    return summary


def delete_objects(client, bucket, keys, log=print):
    for key in keys:
        try:
            client.delete_object(Bucket=bucket, Key=key)
        except Exception as e:
            log(f'  could not delete {key}: {e}')
