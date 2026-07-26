from django_bootstrap import bootstrap
bootstrap()

import csv
import sys

from datetime import datetime

from django.db import models

from appl.models import AdmissionProject

from export_project_options import FIELDS


TRUE_VALUES = ['1', 'true', 'yes', 'y', 't']
FALSE_VALUES = ['0', 'false', 'no', 'n', 'f']

DATE_FORMATS = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

NO_CHANGE = object()


def field_type(field_name):
    return type(AdmissionProject._meta.get_field(field_name))


def parse_boolean(value, field_name):
    if value.lower() in TRUE_VALUES:
        return True
    if value.lower() in FALSE_VALUES:
        return False
    raise ValueError('bad boolean value {} for {}'.format(repr(value),
                                                          field_name))


def parse_date(value, field_name):
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            pass
    raise ValueError('bad date value {} for {}'.format(repr(value),
                                                       field_name))


def parse_value(value, field_name):
    """Returns the parsed value, or NO_CHANGE when the field should be left alone."""
    value = value.strip()
    ftype = field_type(field_name)

    if value == '':
        # empty means None for nullable fields (the interview dates),
        # and "leave unchanged" for the boolean flags
        if AdmissionProject._meta.get_field(field_name).null:
            return None
        else:
            return NO_CHANGE

    if ftype == models.BooleanField:
        return parse_boolean(value, field_name)
    elif ftype == models.DateField:
        return parse_date(value, field_name)
    else:
        return value


def read_rows(filename):
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'id' not in reader.fieldnames:
            raise ValueError('the csv file must have an id column')

        import_fields = [f for f in FIELDS if f in reader.fieldnames]
        return import_fields, list(reader)


def import_row(row, import_fields, dry_run):
    project_id = row['id'].strip()
    try:
        project = AdmissionProject.objects.get(pk=project_id)
    except AdmissionProject.DoesNotExist:
        print('SKIP: project id {} does not exist'.format(project_id))
        return

    title = (row.get('title') or '').strip()
    if title and title != project.title:
        print('WARNING: title mismatch for project {}: {} != {}'.format(
            project_id, repr(title), repr(project.title)))

    changes = []
    for field_name in import_fields:
        value = parse_value(row[field_name], field_name)
        if value is NO_CHANGE:
            continue
        old_value = getattr(project, field_name)
        if old_value != value:
            changes.append((field_name, old_value, value))
            setattr(project, field_name, value)

    if not changes:
        return

    for field_name, old_value, value in changes:
        print('{} [{}]: {}: {} -> {}'.format(project_id,
                                             project.title,
                                             field_name,
                                             old_value,
                                             value))

    if not dry_run:
        project.save(update_fields=[c[0] for c in changes])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    options = [a for a in sys.argv[1:] if a.startswith('--')]

    if len(args) != 1:
        print('usage: python import_project_options.py <options.csv> [--dry-run]')
        sys.exit(1)

    dry_run = '--dry-run' in options

    import_fields, rows = read_rows(args[0])

    print('importing fields: {}'.format(', '.join(import_fields)))
    if dry_run:
        print('(dry run: nothing is saved)')

    for row in rows:
        import_row(row, import_fields, dry_run)


if __name__ == '__main__':
    main()
