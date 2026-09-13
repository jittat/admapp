"""Imports ProjectUploadedDocument slots from a CSV (header row skipped).

Columns: 0 project ids (comma-separated; blank or starting with '-'/'x' skips
the row), 1 rank, 2 title, 3 document_key (rows update the slot with the same
key), 4 descriptions, 5 specifications, 6 notes, 7 allowed_extentions,
8 file_prefix, 9 size_limit, 10 document_type (''/file, 1/url, 2/any),
11 is_required ('0'/'1') or an OR-group requirement_key, 12 is_detail_required,
13 can_have_multiple_files, and optionally 14 major_numbers (e.g. '1,3'),
15 is_late_upload_allowed, 16 validator (e.g. 'tcasfolio').

The whole file is imported in one transaction: an invalid row aborts it.

usage: python import_project_uploaded_documents.py <csv file>
"""
from django_bootstrap import bootstrap
bootstrap()

import csv
import re
import sys

from django.db import transaction

from appl.document_validators import DOCUMENT_VALIDATORS
from appl.models import ProjectUploadedDocument, AdmissionProject

FIELD_MAP = [
    (1, 'rank'),
    (2, 'title'),
    (3, 'document_key'),
    (4, 'descriptions'),
    (5, 'specifications'),
    (6, 'notes'),
    (7, 'allowed_extentions'),
    (8, 'file_prefix'),
]

MAJOR_NUMBERS_RE = re.compile(r'^\d+(,\d+)*$')


class RowError(Exception):
    pass


def cell(items, idx):
    if idx < len(items):
        return items[idx].strip()
    return ''


def is_skipped_row(items):
    project_ids = cell(items, 0)
    return project_ids == '' or project_ids.startswith('-') or project_ids.startswith('x')


def parse_major_numbers(value, project_ids):
    major_numbers = value.replace(' ', '')
    if major_numbers == '':
        return ''
    if not MAJOR_NUMBERS_RE.match(major_numbers):
        raise RowError(f'invalid major_numbers {value!r}')
    if len(project_ids) != 1:
        raise RowError('major_numbers are per project; the row must list exactly one project')
    return major_numbers


def import_row(items):
    project_ids = [p.strip() for p in cell(items, 0).split(',') if p.strip() != '']
    requirement = cell(items, 11)

    if requirement.startswith('if'):
        raise RowError(f'conditional requirement key {requirement!r} is no longer supported; '
                       'use the major_numbers column')

    major_numbers = parse_major_numbers(cell(items, 14), project_ids)

    validator = cell(items, 16)
    if validator != '' and validator not in DOCUMENT_VALIDATORS:
        raise RowError(f'unknown validator {validator!r}')

    projects = []
    for p in project_ids:
        try:
            projects.append(AdmissionProject.objects.get(pk=p))
        except (AdmissionProject.DoesNotExist, ValueError):
            raise RowError(f'unknown project id {p!r}')

    document_key = items[3]

    old_documents = ProjectUploadedDocument.objects.filter(document_key=document_key).all()
    if old_documents:
        document = old_documents[0]
    else:
        document = ProjectUploadedDocument()

    for idx, f in FIELD_MAP:
        setattr(document, f, items[idx])

    document.size_limit = int(items[9])
    document_type_value = items[10].strip()
    if document_type_value in ['1', 'url']:
        document.document_type = ProjectUploadedDocument.DOCUMENT_TYPE_URL
    elif document_type_value in ['2', 'any']:
        document.document_type = ProjectUploadedDocument.DOCUMENT_TYPE_ANY
    else:
        document.document_type = ProjectUploadedDocument.DOCUMENT_TYPE_FILE
    document.is_required = (requirement == '1')
    document.is_detail_required = (items[12].strip() == '1')
    document.can_have_multiple_files = (items[13].strip() == '1')

    if requirement not in ['0', '1']:
        document.requirement_key = requirement

    document.major_numbers = major_numbers
    document.is_late_upload_allowed = (cell(items, 15) == '1')
    document.validator = validator

    document.save()

    for project in projects:
        document.admission_projects.add(project)

    return document


@transaction.atomic
def import_rows(lines):
    counter = 0
    for line_number, items in enumerate(lines[1:], start=2):
        if is_skipped_row(items):
            continue
        try:
            import_row(items)
        except RowError as e:
            raise RowError(f'line {line_number}: {e}')
        counter += 1
    return counter


def main():
    filename = sys.argv[1]
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        lines = [l for l in reader]

    try:
        counter = import_rows(lines)
    except RowError as e:
        print('ERROR', e, '- nothing imported')
        sys.exit(1)

    print('Imported',counter,'project documents')


if __name__ == '__main__':
    main()
