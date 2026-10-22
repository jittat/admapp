#!/usr/bin/env python3
"""
Build zips of a project's portfolios, one set per major, and upload them to
the private S3_PORTFOLIO_BUCKET_NAME bucket (see
docs/portfolio-bulk-download.md).

For each major: the paid applicants, ordered by name as in the backoffice,
are split into batches of --batch-size; each batch becomes one zip, streamed
straight to S3 (nothing is written to local disk) and recorded as a
backoffice.PortfolioZipFile row. A zip holds one file per uploaded document
of the slot, named <seq>_<national_id>_<first>_<last>[_2].<ext>, plus an
index.csv listing every applicant and what happened to each document.

Files come from MEDIA_ROOT, from the encrypted S3 media backup when missing
locally, or, for TCASFolio links, from the mirrored PDF behind
local_document_url (LOCAL_DOCUMENT_BASE_PATH / LOCAL_DOCUMENT_BASE_URL).

A major that already has zips is skipped (so re-running after a failure
continues with the rest); --rebuild builds it again and deletes the old zips.
A major is recorded only when all its batches uploaded; on an error its
partial uploads are deleted and the script moves on to the next major.

Usage (from the scripts directory):
    python build_portfolio_zips.py [options] <project_id> <round_id> <document_key>

    --major N [N ...]  only these major numbers (default: all majors)
    --batch-size N     applicants per zip (default: PORTFOLIO_ZIP_BATCH_SIZE)
    --dry-run          print the planned batches and file names; no upload
    --rebuild          rebuild majors that already have zips
"""
import argparse
import sys

from django_bootstrap import bootstrap

bootstrap()

from django.conf import settings

from appl.models import AdmissionProject, AdmissionRound, Major
from backoffice import portfolio_zips as pz


def print_dry_run(project, admission_round, major, pud, batch_size):
    applicants = pz.load_paid_applicants_by_name(project, admission_round, major)
    documents = pz.load_documents_by_applicant(applicants, pud)
    plan = pz.plan_major(applicants, documents, batch_size)

    status_counts = {}
    print(f'  {len(applicants)} paid applicants, {len(plan)} batch(es)')
    for batch_number, items in enumerate(plan, start=1):
        print(f'  batch {batch_number}: seq {items[0][0]}-{items[-1][0]}')
        for seq, applicant, files in items:
            for name, status in files:
                status_counts[status] = status_counts.get(status, 0) + 1
                label = name or f'({applicant.national_id} '\
                                f'{pz.applicant_display_name(applicant)}: no file)'
                print(f'    {status:15} {label}')
    print(f'  statuses: {format_counts(status_counts)}')


def format_counts(counts):
    return ', '.join(f'{k} {v}' for k, v in sorted(counts.items())) or '-'


def check_settings():
    missing = [name for name in ('S3_PORTFOLIO_BUCKET_NAME',
                                 'S3_PORTFOLIO_ACCESS_KEY',
                                 'S3_PORTFOLIO_SECRET_KEY',
                                 'S3_PORTFOLIO_ENDPOINT')
               if not getattr(settings, name, '')]
    if missing:
        sys.exit(f'Missing settings: {", ".join(missing)}')
    if not settings.LOCAL_DOCUMENT_BASE_PATH or not settings.LOCAL_DOCUMENT_BASE_URL:
        print('Warning: LOCAL_DOCUMENT_BASE_PATH/URL not set; '
              'mirrored TCASFolio PDFs will be reported as mirror-missing.')


def main():
    parser = argparse.ArgumentParser(
        description='Build portfolio zips per major and upload them to S3.')
    parser.add_argument('project_id', type=int)
    parser.add_argument('round_id', type=int)
    parser.add_argument('document_key',
                        help='document_key of the portfolio ProjectUploadedDocument')
    parser.add_argument('--major', type=int, nargs='+', metavar='N',
                        help='only these major numbers')
    parser.add_argument('--batch-size', type=int,
                        default=settings.PORTFOLIO_ZIP_BATCH_SIZE)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rebuild', action='store_true')
    args = parser.parse_args()

    if args.batch_size < 1:
        sys.exit('--batch-size must be at least 1')

    project = AdmissionProject.objects.get(pk=args.project_id)
    admission_round = AdmissionRound.objects.get(pk=args.round_id)
    try:
        pud = pz.find_project_uploaded_document(project, args.document_key)
    except ValueError as e:
        sys.exit(str(e))

    majors = list(Major.objects.filter(admission_project=project).order_by('number'))
    if args.major:
        wanted = set(args.major)
        unknown = wanted - {m.number for m in majors}
        if unknown:
            sys.exit(f'Unknown major number(s): {sorted(unknown)}')
        majors = [m for m in majors if m.number in wanted]

    print(f'Project {project.id} {project.title} / round {admission_round.id} / '
          f'slot {pud.id} {pud.title} / batch size {args.batch_size}')

    if args.dry_run:
        for major in majors:
            print(f'Major {major.number} {major.title}')
            print_dry_run(project, admission_round, major, pud, args.batch_size)
        return

    check_settings()
    client = pz.get_portfolio_s3_client()
    bucket = settings.S3_PORTFOLIO_BUCKET_NAME

    built, skipped, empty, failed = [], [], [], []
    missing_rows = []
    for major in majors:
        print(f'Major {major.number} {major.title}')
        try:
            summary = pz.build_major_zips(project, admission_round, major, pud,
                                          client, bucket, args.batch_size,
                                          rebuild=args.rebuild)
        except Exception as e:
            print(f'  FAILED: {type(e).__name__}: {e}')
            failed.append(major)
            continue

        if summary['skipped']:
            print('  already built, skipped (use --rebuild to build again)')
            skipped.append(major)
        elif summary['batches'] == 0:
            print('  no paid applicants, nothing uploaded')
            empty.append(major)
        else:
            print(f'  {summary["applicant_count"]} applicants, '
                  f'{summary["file_count"]} files, '
                  f'{summary["missing_count"]} without a file, '
                  f'{summary["batches"]} zip(s), {summary["size"]:,} bytes')
            print(f'  statuses: {format_counts(summary["status_counts"])}')
            built.append(major)
            missing_rows += [(major, r) for r in summary['missing_rows']]

    print()
    print(f'Built {len(built)}, skipped {len(skipped)}, '
          f'no applicants {len(empty)}, failed {len(failed)}')
    if failed:
        print('Failed majors: ' + ', '.join(str(m.number) for m in failed))
    if missing_rows:
        print()
        print('Documents not in the zips:')
        for major, r in missing_rows:
            print(f'  major {major.number} seq {r["seq"]} {r["national_id"]} '
                  f'{r["first_name"]} {r["last_name"]}: {r["status"]} '
                  f'{r["document_url"]}'.rstrip())
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
