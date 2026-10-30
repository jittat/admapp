#!/usr/bin/env python3
"""
Replace applicants' uploaded files with links, from a CSV of updates.

For one project and major, finds the project's file-or-link slot shown to
that major and, for each CSV row, turns the applicant's single document in
that slot from a file into a link. The old file stays on disk and is
recorded in UploadedDocument.replaced_uploaded_file; local_document_url is
cleared, so run fetch_mytcasfolio_pdf.py afterwards to mirror the new
TCASFolio links.

Nothing is written unless --apply is given (--dry-run, the default, only
reports what would change; the two cannot be combined). Rows are refused (and reported)
when the applicant is not found, has no active application to the project
with the major selected, the url fails the slot's checks, or the slot holds
no or several documents. A document that is already a link is not changed:
the same url is reported as already done, a different one as a warning.

Usage (run from the scripts/ directory, inside the project's virtualenv):
    python replace_uploaded_files_with_urls.py --project ID --major N updates.csv [--dry-run]
    python replace_uploaded_files_with_urls.py --project ID --major N updates.csv --apply
    (add --slot KEY, the slot's document_key, when the project has several
    file-or-link slots for the major, and --report FILE to write the results
    as a CSV)

    updates.csv  columns national_id,url (a header row with those names is
                 optional)

See docs/uploaded-documents.md.
"""

from django_bootstrap import bootstrap
bootstrap()

import argparse
import csv
import sys

from appl.models import AdmissionProject
from maintenance.document_url_replacement import (
    REPLACED, TO_REPLACE, URL_MISMATCH,
    SetupError, describe_slot, replace_files_with_urls)

REPORT_FIELDS = ['national_id', 'applicant', 'document_id', 'status',
                 'old_file', 'url', 'current_url', 'message']


def read_updates(filename):
    updates = []
    with open(filename, encoding='utf-8-sig', newline='') as f:
        for i, row in enumerate(csv.reader(f)):
            if not row or not ''.join(row).strip():
                continue
            if i == 0 and row[0].strip().lower() == 'national_id':
                continue
            if len(row) < 2:
                raise ValueError(f'line {i + 1}: expected national_id,url')
            updates.append((row[0], row[1]))
    return updates


def report_row(r):
    return {
        'national_id': r.national_id,
        'applicant': str(r.applicant) if r.applicant else '',
        'document_id': r.document.id if r.document else '',
        'status': r.status,
        'old_file': r.old_file,
        'url': r.url,
        'current_url': r.current_url,
        'message': r.message,
    }


def describe(r):
    who = f'{r.national_id} {r.applicant}' if r.applicant else r.national_id
    line = f'{r.status}: {who}'
    if r.document:
        line += f' (document {r.document.id})'
    if r.old_file:
        line += f'\n  file: {r.old_file}\n  url:  {r.url}'
    if r.current_url and r.status == URL_MISMATCH:
        line += f'\n  current url: {r.current_url}\n  csv url:     {r.url}'
    if r.message:
        line += f'\n  {r.message}'
    return line


def main():
    parser = argparse.ArgumentParser(
        description='Replace uploaded files with links in a file-or-link slot.')
    parser.add_argument('csv_file', help='CSV with columns national_id,url')
    parser.add_argument('--project', type=int, required=True, metavar='ID')
    parser.add_argument('--major', type=int, required=True, metavar='N',
                        help='major number in the project')
    parser.add_argument('--slot', metavar='KEY',
                        help='document_key of the ProjectUploadedDocument, when there '
                             'are several candidates')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true',
                      help='only report what would change (the default)')
    mode.add_argument('--apply', action='store_true',
                      help='write the changes')
    parser.add_argument('--report', metavar='FILE',
                        help='also write the results as a CSV (UTF-8 with BOM)')
    args = parser.parse_args()

    project = AdmissionProject.objects.filter(pk=args.project).first()
    if project is None:
        parser.error(f'no project with id {args.project}')

    try:
        updates = read_updates(args.csv_file)
    except ValueError as e:
        parser.error(str(e))

    try:
        slot, results = replace_files_with_urls(project, args.major, updates,
                                                document_key=args.slot, apply=args.apply)
    except SetupError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'Project {project.id} {project.title}, major {args.major}, '
          f'slot {describe_slot(slot)}; {len(updates)} rows'
          + ('' if args.apply else ' -- DRY RUN, nothing written'))
    print()

    for r in results:
        # already-done rows are only counted in the summary (and the report)
        if r.status in (REPLACED, TO_REPLACE):
            print(describe(r))

    problems = [r for r in results if r.is_warning or r.is_error]
    if problems:
        print()
        print('Warnings and errors (not changed):')
        for r in problems:
            print(describe(r))

    counts = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    print()
    print('Summary: ' + (', '.join(f'{status} {n}' for status, n in sorted(counts.items()))
                         or 'no rows'))
    if not args.apply and counts.get(TO_REPLACE):
        print('Run again with --apply to write the changes.')

    if args.report:
        with open(args.report, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
            writer.writeheader()
            writer.writerows(report_row(r) for r in results)
        print(f'Report written to {args.report}')


if __name__ == '__main__':
    main()
