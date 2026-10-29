#!/usr/bin/env python3
"""
Mirror TCASFolio PDFs linked from uploaded documents to local storage.

Applicants can submit a TCASFolio link instead of a file (see
docs/uploaded-documents.md). This script downloads the PDF behind each
such link so staff can open a local copy: for every UploadedDocument whose
document_url contains 'mytcas.com' and whose local_document_url is still
blank, it

  1. logs in to the TCASFolio admin API (folio-admins) and asks for the
     folio's PDF (a pre-signed S3 URL),
  2. saves it as <base_path>/<random 10-digit prefix>-<folio id>.pdf,
  3. sets local_document_url to <base_url>/<that filename>.

The staff applicant page then links to local_document_url instead of
document_url. Documents that already have a local_document_url are skipped,
so the script is safe to re-run.

With --refresh, already-mirrored documents are downloaded again as well and
compared byte-for-byte with the local copy; a changed PDF replaces it under
the same filename (so local_document_url is unchanged), and the old copy is
kept as <filename>.<YYYYmmdd-HHMMSS>.bak. A missing local copy is written
back. Not-yet-mirrored documents are mirrored as usual. At the end it prints
a report of the updated / new / restored / failed documents: the applicant,
the document slot, the applicant's applications to the slot's projects (with
the selected majors), and the file sizes.

Fetched links are https://folio.mytcas.com/... (the /_/<id> short-link
form, or /view-folio/<id>) and https://student.mytcas.com/view-folio/<id>;
others are reported as "wrong url". The folio id is the last path segment.

Usage (run from the scripts/ directory, inside the project's virtualenv):
    python fetch_mytcasfolio_pdf.py <base_path> <base_url>
    python fetch_mytcasfolio_pdf.py --dry-run [--limit N]
    python fetch_mytcasfolio_pdf.py --refresh [--report FILE] <base_path> <base_url>
    (any of these can add --project ID [--major N [N ...]])

    base_path  directory to save the PDFs in
    base_url   public URL that serves base_path (a trailing / is dropped)
    --dry-run  fetch a random sample of N (default 10) not-yet-mirrored
               documents into memory and report size / PDF check; nothing
               is saved and no document is updated (base_path/base_url are
               not needed). The token cache below is still written.
    --refresh  re-download every document, replacing local copies that
               changed (see above)
    --report   with --refresh, also write the report rows to FILE as CSV
               (UTF-8 with BOM, so Excel shows Thai correctly)
    --project ID
               only documents of applicants with an active (not canceled)
               application to this project, in any round, and only in the
               project's own document slots and common slots. Works with
               every mode above.
    --major N [N ...]
               with --project, only applicants that selected any of these
               major numbers (slot major_numbers restrictions are ignored)

Files (both in the current directory):
    - .mytcas-env with TCAS_EMAIL and TCAS_PASSWORD (a TCASFolio admin
      account)
    - mytcas-token.json is written here to cache the access token
      (TOKEN_EXPIRY_DAYS days); delete it to force a new login
"""

from django_bootstrap import bootstrap
bootstrap()

import sys

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from appl.models import AdmissionProject, MajorSelection, UploadedDocument

import argparse
import csv
import json
import sys
import os
import re
import shutil
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Configuration
API_BASE_URL = "https://tcas65.as.r.appspot.com"
LOGIN_ENDPOINT = "/folio-admins/login"
VERIFY_ENDPOINT = "/folio-admins/me"
PDF_BASE_URL = "https://tcas-pdf-dot-tcas65.as.r.appspot.com"
TOKEN_FILE = "mytcas-token.json"
TOKEN_EXPIRY_DAYS = 2
PDF_REQUEST_DELAY = 1  # seconds between PDF requests

# Request headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/json',
    'Origin': 'https://student.mytcas.com',
    'Referer': 'https://student.mytcas.com/',
    'Connection': 'keep-alive'
}


class TCASFetcher:
    """Handle TCAS FOLIO authentication and PDF fetching."""

    def __init__(self, email=None, password=None):
        """Initialize fetcher with credentials."""
        load_dotenv(".mytcas-env")

        self.email = email or os.getenv("TCAS_EMAIL")
        self.password = password or os.getenv("TCAS_PASSWORD")

        if not self.email or not self.password:
            raise ValueError(
                "Missing credentials. Please set TCAS_EMAIL and TCAS_PASSWORD "
                "in .env file or pass them to constructor"
            )

        self.session = requests.Session()
        self.last_pdf_request_time = None
        self.access_token = None
        self.token_expiry = None

    def login(self):
        """
        Login to TCAS FOLIO and obtain access token.

        Returns:
            bool: True if login successful, False otherwise
        """
        login_url = f"{API_BASE_URL}{LOGIN_ENDPOINT}"

        payload = {
            "email": self.email,
            "password": self.password
        }

        try:
            response = self.session.post(
                login_url,
                headers=HEADERS,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('accessToken')

                if self.access_token:
                    self.token_expiry = datetime.now() + timedelta(days=TOKEN_EXPIRY_DAYS)
                    self._save_token()
                    print(f"✓ Login successful for {self.email}")
                    return True
                else:
                    print("✗ Login failed: No access token received")
                    return False
            else:
                print(f"✗ Login failed: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Login error: {e}")
            return False

    def verify_token(self):
        """
        Verify if the current access token is valid.

        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self.access_token:
            return False

        verify_url = f"{API_BASE_URL}{VERIFY_ENDPOINT}"

        try:
            response = self.session.get(
                verify_url,
                headers={
                    **HEADERS,
                    'accessToken': self.access_token
                }
            )

            return response.status_code == 200

        except requests.exceptions.RequestException as e:
            print(f"✗ Token verification error: {e}")
            return False

    def ensure_authenticated(self):
        """
        Ensure user is authenticated. Try to load saved token first,
        then verify it. If invalid, perform a new login.

        Returns:
            bool: True if authenticated, False otherwise
        """
        # Try to load saved token
        if self._load_token():
            # Check if token is expired
            if self.token_expiry and datetime.now() < self.token_expiry:
                # Verify token with API
                if self.verify_token():
                    #print("✓ Using saved token")
                    return True
                else:
                    print("Saved token is invalid, logging in again...")
            else:
                print("Token has expired, logging in again...")

        # If no valid token, perform login
        return self.login()

    def fetch_pdf_url(self, folio_id):
        """
        Fetch PDF URL for a given folio ID.

        Args:
            folio_id: The folio identifier (e.g., '68e3880b2ef4c36c489acfc1_199e7dca88e')

        Returns:
            dict: JSON response containing PDF URL, or None if failed
        """
        if not self.access_token:
            print("✗ Not authenticated. Call ensure_authenticated() first.")
            return None

        pdf_url = f"{PDF_BASE_URL}/folios/{folio_id}/get-pdf"

        headers = {
            **HEADERS,
            'accessToken': self.access_token,
            'Content-Length': '0'
        }

        if self.last_pdf_request_time is not None:
            wait = PDF_REQUEST_DELAY - (time.monotonic() - self.last_pdf_request_time)
            if wait > 0:
                time.sleep(wait)
        self.last_pdf_request_time = time.monotonic()

        try:
            response = self.session.post(pdf_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                #print(f"✓ PDF URL fetched successfully")
                return data
            else:
                print(f"✗ Failed to fetch PDF URL: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"✗ Fetch error: {e}")
            return None

    def _save_token(self):
        """Save access token to file for persistence."""
        token_data = {
            'access_token': self.access_token,
            'expiry': self.token_expiry.isoformat() if self.token_expiry else None
        }

        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)

    def _load_token(self):
        """
        Load access token from file.

        Returns:
            bool: True if token loaded successfully, False otherwise
        """
        token_file = Path(TOKEN_FILE)

        if not token_file.exists():
            return False

        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)

            self.access_token = token_data.get('access_token')
            expiry_str = token_data.get('expiry')

            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)

            return True

        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Error loading token: {e}")
            return False

    def download_pdf(self, pdf_url):
        """
        Download PDF from S3 URL.

        Args:
            pdf_url: The S3 pre-signed URL for the PDF

        Returns:
            bytes: The PDF content, or None if failed
        """
        try:
            response = self.session.get(pdf_url)
        except requests.exceptions.RequestException as e:
            print(f"✗ Download error: {e}")
            return None

        if response.status_code != 200:
            print(f"✗ Failed to download PDF: HTTP {response.status_code}")
            return None

        return response.content


def extract_folio_id(url):
    """
    Extract folio ID from URL.

    Args:
        url: Full URL or just folio ID

    Returns:
        str: Extracted folio ID

    Examples:
        'https://folio.mytcas.com/_/68e3880c2ef4c36c489ad051_19a3d2b7c42'
        -> '68e3880c2ef4c36c489ad051_19a3d2b7c42'

        'https://student.mytcas.com/view-folio/68e3880c2ef4c36c489ad051'
        -> '68e3880c2ef4c36c489ad051'

        'https://tcas-pdf-dot-tcas65.as.r.appspot.com/folios/68e3880b2ef4c36c489acfc1_199e7dca88e/get-pdf'
        -> '68e3880b2ef4c36c489acfc1_199e7dca88e'
    """
    # Try to extract from view-folio URL pattern (/view-folio/ID), used on
    # both student.mytcas.com and folio.mytcas.com
    match = re.search(r'/view-folio/([^/?#]+)', url)
    if match:
        return match.group(1)

    # Try to extract from folio.mytcas.com URL pattern (/_/ID)
    match = re.search(r'/_/([^/]+)', url)
    if match:
        return match.group(1)

    # Try to extract from tcas-pdf URL pattern (/folios/ID/get-pdf)
    match = re.search(r'/folios/([^/]+)(?:/get-pdf)?', url)
    if match:
        return match.group(1)

    # If no match, assume it's already a folio ID
    return url


_fetcher = None


def get_fetcher():
    """Return a TCASFetcher authenticated once for the whole run."""
    global _fetcher
    if _fetcher is None:
        try:
            fetcher = TCASFetcher()
        except ValueError as e:
            print(f"✗ Configuration error: {e}")
            sys.exit(1)

        if not fetcher.ensure_authenticated():
            print("✗ Authentication failed")
            sys.exit(1)

        _fetcher = fetcher
    return _fetcher


def fetch_pdf_main(url):
    """Fetch the PDF behind a TCASFolio link. Returns its bytes, or None."""
    folio_id = extract_folio_id(url)
    fetcher = get_fetcher()

    try:
        result = fetcher.fetch_pdf_url(folio_id)
        if not result:
            print("✗ Failed to fetch PDF URL")
            return None
        if 'pdf' not in result:
            return None

        content = fetcher.download_pdf(result['pdf'])
        if not content:
            print("✗ Failed to download PDF")
            return None

        return content

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


FOLIO_URL_PREFIXES = (
    'https://folio.mytcas.com/',
    'https://student.mytcas.com/view-folio/',
)


def random_prefix(length=10):
    import random
    import string
    letters = string.digits
    return ''.join(random.choice(letters) for i in range(length))


def write_file(path, content):
    """Write content to path atomically (temp file, then os.replace)."""
    tmp_path = f'{path}.tmp'
    with open(tmp_path, 'wb') as f:
        f.write(content)
    os.replace(tmp_path, path)


def mirror_document(d, document_url, base_path, base_url):
    """
    Download the PDF of a not-yet-mirrored document to a new file and set
    its local_document_url. Returns (filename, content), or None.
    """
    content = fetch_pdf_main(document_url)
    if not content:
        return None

    filename = f'{random_prefix()}-{extract_folio_id(document_url)}.pdf'
    with open(f'{base_path}/{filename}', 'wb') as f:
        f.write(content)

    d.local_document_url = f'{base_url}/{filename}'
    print(f'URL: {d.local_document_url}')
    d.save()
    return filename, content


def dry_run_fetch(pending, limit):
    import random
    sample = random.sample(pending, min(limit, len(pending)))
    print(f'DRY RUN: fetching {len(sample)} of {len(pending)} not-yet-mirrored '
          'documents (nothing is saved)')

    fetched = 0
    for d, document_url in sample:
        print(d.applicant, document_url)
        content = fetch_pdf_main(document_url)

        if not content:
            print('ERROR: cannot fetch pdf for', d.applicant, document_url)
            continue

        is_pdf = content.startswith(b'%PDF')
        print(f'  {len(content)} bytes, {"PDF" if is_pdf else "NOT A PDF"}')
        if is_pdf:
            fetched += 1

    print(f'DRY RUN: {fetched}/{len(sample)} fetched as PDF')


# --refresh statuses, in report order
REFRESH_STATUSES = ['updated', 'new', 'restored', 'failed', 'unchanged']
REPORTED_STATUSES = ['updated', 'new', 'restored', 'failed']


def refresh_document(d, document_url, base_path, base_url, backup_suffix):
    """
    Re-download the PDF of a document and replace the local copy if it
    changed (the old copy is kept as <file>.<backup_suffix>.bak). A document
    without a local copy is mirrored as usual.

    Returns a dict with 'status' (one of REFRESH_STATUSES) and file details.
    """
    if d.local_document_url == '':
        result = mirror_document(d, document_url, base_path, base_url)
        if not result:
            return {'status': 'failed', 'note': 'cannot fetch pdf'}
        filename, content = result
        return {'status': 'new', 'filename': filename,
                'new_size': len(content)}

    url_prefix = f'{base_url}/'
    filename = d.local_document_url[len(url_prefix):]
    if (not d.local_document_url.startswith(url_prefix)
            or filename == '' or '/' in filename):
        return {'status': 'failed',
                'note': 'local_document_url is not under base_url'}
    path = f'{base_path}/{filename}'

    content = fetch_pdf_main(document_url)
    if not content:
        return {'status': 'failed', 'filename': filename,
                'note': 'cannot fetch pdf'}
    if not content.startswith(b'%PDF'):
        return {'status': 'failed', 'filename': filename,
                'new_size': len(content), 'note': 'not a PDF'}

    if not os.path.exists(path):
        write_file(path, content)
        return {'status': 'restored', 'filename': filename,
                'new_size': len(content), 'note': 'local file was missing'}

    with open(path, 'rb') as f:
        old_content = f.read()

    # Assumes TCASFolio PDFs are byte-stable (the same folio gives the same
    # bytes on every fetch); if not, every document would show as updated.
    if old_content == content:
        return {'status': 'unchanged', 'filename': filename,
                'old_size': len(old_content), 'new_size': len(content)}

    backup_filename = f'{filename}.{backup_suffix}.bak'
    shutil.copy2(path, f'{base_path}/{backup_filename}')
    write_file(path, content)
    return {'status': 'updated', 'filename': filename,
            'old_size': len(old_content), 'new_size': len(content),
            'backup_filename': backup_filename}


def applicant_projects(d):
    """
    The applicant's active applications to the projects of the document's
    slot (all active applications if the slot lists no project), as
    'project / round [major, ...]' strings.
    """
    project_ids = set(d.project_uploaded_document.admission_projects
                      .values_list('id', flat=True))
    applications = (d.applicant.get_all_active_applications()
                    .select_related('admission_project', 'admission_round'))

    items = []
    for application in applications:
        if project_ids and application.admission_project_id not in project_ids:
            continue

        try:
            majors = application.major_selection.get_majors()
        except (ObjectDoesNotExist, ValueError):
            majors = []
        major_titles = ', '.join(f'{m.number} {m.title}'
                                 for m in majors if m)

        items.append(f'{application.admission_project.title} / '
                     f'{application.admission_round} [{major_titles}]')
    return '; '.join(items)


REPORT_FIELDS = [
    'status', 'applicant_id', 'national_id', 'name', 'email',
    'document_id', 'document_title', 'projects',
    'filename', 'old_size', 'new_size', 'backup_filename',
    'local_document_url', 'document_url', 'note',
]


def report_row(d, document_url, result):
    applicant = d.applicant
    return {
        'status': result['status'],
        'applicant_id': applicant.id,
        'national_id': applicant.passport_number or applicant.national_id,
        'name': applicant.get_full_name(),
        'email': applicant.email,
        'document_id': d.id,
        'document_title': d.project_uploaded_document.title,
        'projects': applicant_projects(d),
        'filename': result.get('filename', ''),
        'old_size': result.get('old_size', ''),
        'new_size': result.get('new_size', ''),
        'backup_filename': result.get('backup_filename', ''),
        'local_document_url': d.local_document_url,
        'document_url': document_url,
        'note': result.get('note', ''),
    }


def refresh_fetch(pending, base_path, base_url, report_filename=None):
    backup_suffix = datetime.now().strftime('%Y%m%d-%H%M%S')
    counts = {status: 0 for status in REFRESH_STATUSES}
    rows = []

    for d, document_url in pending:
        print(d.applicant, document_url)
        result = refresh_document(d, document_url, base_path, base_url,
                                  backup_suffix)
        status = result['status']
        counts[status] += 1
        print(f'  {status}', result.get('note', ''))

        if status in REPORTED_STATUSES:
            rows.append(report_row(d, document_url, result))

    print()
    print('REFRESH SUMMARY:',
          ', '.join(f'{status} {counts[status]}' for status in REFRESH_STATUSES))

    rows.sort(key=lambda row: REPORTED_STATUSES.index(row['status']))
    for row in rows:
        print()
        print(f"[{row['status']}] {row['name']} ({row['national_id']}, "
              f"applicant {row['applicant_id']}, {row['email']})")
        print(f"  document: {row['document_title']} (id {row['document_id']})")
        print(f"  projects: {row['projects']}")
        if row['filename']:
            print(f"  file: {row['filename']} "
                  f"{row['old_size']} -> {row['new_size']} bytes"
                  + (f", old copy: {row['backup_filename']}"
                     if row['backup_filename'] else ''))
        if row['note']:
            print(f"  note: {row['note']}")

    if report_filename:
        with open(report_filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print()
        print(f'Report written to {report_filename}')


def select_applicant_ids(project, major_numbers=None):
    """
    Ids of applicants with an active application to project (in any round)
    that selected any of major_numbers (any major if not given).
    """
    selections = (MajorSelection.objects
                  .filter(admission_project=project,
                          project_application__is_canceled=False))
    if not major_numbers:
        return set(selections.values_list('applicant_id', flat=True))

    wanted = set(major_numbers)
    return {s.applicant_id for s in selections
            if wanted.intersection(s.get_major_numbers())}


def apply_project_filter(documents, project, major_numbers):
    """
    Limit documents to the selected applicants, in the project's own slots
    and common slots.
    """
    applicant_ids = select_applicant_ids(project, major_numbers)
    documents = (documents
                 .filter(applicant_id__in=applicant_ids)
                 .filter(Q(project_uploaded_document__admission_projects=project) |
                         Q(project_uploaded_document__is_common_document=True))
                 .distinct())

    majors = (f', majors {", ".join(str(n) for n in major_numbers)}'
              if major_numbers else '')
    print(f'Project {project.id} {project.title}{majors}: '
          f'{len(applicant_ids)} applicants, '
          f'{documents.count()} TCASFolio documents')
    return documents


def main():
    parser = argparse.ArgumentParser(
        description='Mirror TCASFolio PDFs linked from uploaded documents.')
    parser.add_argument('base_path', nargs='?',
                        help='directory to save the PDFs in')
    parser.add_argument('base_url', nargs='?',
                        help='public URL that serves base_path')
    parser.add_argument('--dry-run', action='store_true',
                        help='fetch a random sample into memory only; save nothing')
    parser.add_argument('--limit', type=int, default=10,
                        help='number of documents to fetch in a dry run (default 10)')
    parser.add_argument('--refresh', action='store_true',
                        help='re-download all documents and replace local copies that changed')
    parser.add_argument('--report',
                        help='with --refresh, also write the report to this CSV file')
    parser.add_argument('--project', type=int, metavar='ID',
                        help='only applicants with an active application to this '
                        'project (any round), in its slots and common slots')
    parser.add_argument('--major', type=int, nargs='+', metavar='N',
                        help='with --project, only applicants that selected any '
                        'of these major numbers')
    args = parser.parse_args()

    if args.dry_run and args.refresh:
        parser.error('--dry-run cannot be used with --refresh')
    if args.report and not args.refresh:
        parser.error('--report requires --refresh')
    if not args.dry_run and not (args.base_path and args.base_url):
        parser.error('base_path and base_url are required unless --dry-run')
    if args.major and args.project is None:
        parser.error('--major requires --project')

    project = None
    if args.project is not None:
        project = AdmissionProject.objects.filter(pk=args.project).first()
        if project is None:
            parser.error(f'no project with id {args.project}')
        if args.major:
            known = set(project.major_set.values_list('number', flat=True))
            unknown = [n for n in args.major if n not in known]
            if unknown:
                parser.error(f'project {project.id} has no major '
                             f'{", ".join(str(n) for n in unknown)}')

    documents = (UploadedDocument.objects
                 .filter(document_url__contains='mytcas.com')
                 .select_related('applicant', 'project_uploaded_document')
                 .all())
    if project is not None:
        documents = apply_project_filter(documents, project, args.major)

    pending = []
    for d in documents:
        if d.local_document_url != '' and not args.refresh:
            continue

        document_url = d.document_url.strip()
        if not document_url.startswith(FOLIO_URL_PREFIXES):
            print('ERROR: wrong url:', d.applicant, document_url)
            continue

        pending.append((d, document_url))

    if args.dry_run:
        dry_run_fetch(pending, args.limit)
        return

    base_path = args.base_path
    base_url = args.base_url
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    if args.refresh:
        refresh_fetch(pending, base_path, base_url, args.report)
        return

    for d, document_url in pending:
        print(d.applicant, d.document_url)
        if not mirror_document(d, document_url, base_path, base_url):
            print('ERROR: cannot fetch pdf for', d.applicant, document_url)

if __name__ == '__main__':
    main()
