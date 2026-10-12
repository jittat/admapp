"""
Import CUPT export custom projects and additional project rules.

Reads a JSON file of the form

    {"additional_projects": [
        [cupt_code, title],
        ...
     ],
     "rules": [
        [cupt_code, program_major_codes, rule_json],
        ...
     ]}

and, for the admission project given on the command line,

  1. upserts each additional project as a CuptExportCustomProject (matched
     by cupt_code; the title is updated),
  2. upserts each rule as a CuptExportAdditionalProjectRule of that
     admission project, pointing at the CuptExportCustomProject with the
     rule's cupt_code (which may come from this file or already be in the
     database).

program_major_codes is either a comma-separated string or a list of codes,
in the stored form (no project cupt code prefix). rule_json is either a
JSON object or a string containing JSON.

An existing rule is the same rule when it has the same admission project,
the same custom project and the same set of program major codes (spacing
and order are ignored); its rule_json is then updated. Nothing is ever
deleted: existing rules of the project that no rule in the file matched
are listed at the end, so stale ones can be removed in the admin.

Everything runs in one transaction; any bad row aborts the whole import.

Usage (run from the scripts/ directory, inside the project's virtualenv):
    python import_cupt_export_custom_projects.py [--dry-run] <project_id> <json_file>

    --dry-run  report what would be created/updated without saving
"""

from django_bootstrap import bootstrap
bootstrap()

import argparse
import json
import sys

from django.db import transaction

from appl.models import AdmissionProject
from criteria.models import CuptExportCustomProject, CuptExportAdditionalProjectRule


class ImportError_(Exception):
    pass


def split_codes(program_major_codes):
    if isinstance(program_major_codes, str):
        program_major_codes = program_major_codes.split(',')
    return [str(c).strip() for c in program_major_codes if str(c).strip() != '']


def parse_additional_projects(config):
    projects = []
    for i, items in enumerate(config.get('additional_projects', []), start=1):
        if not isinstance(items, list) or len(items) != 2:
            raise ImportError_(f'additional_projects #{i}: expected [cupt_code, title]')
        cupt_code = str(items[0]).strip()
        title = str(items[1]).strip()
        if cupt_code == '' or title == '':
            raise ImportError_(f'additional_projects #{i}: blank cupt_code or title')
        projects.append((cupt_code, title))
    return projects


def parse_rules(config):
    rules = []
    for i, items in enumerate(config.get('rules', []), start=1):
        if not isinstance(items, list) or len(items) != 3:
            raise ImportError_(f'rules #{i}: expected [cupt_code, program_major_codes, rule_json]')
        cupt_code = str(items[0]).strip()
        if cupt_code == '':
            raise ImportError_(f'rules #{i}: blank cupt_code')

        if not isinstance(items[1], (str, list)):
            raise ImportError_(f'rules #{i}: program_major_codes must be a string or a list')
        codes = split_codes(items[1])
        if len(codes) == 0:
            raise ImportError_(f'rules #{i}: no program major codes')

        if isinstance(items[2], str):
            rule_json = items[2].strip()
            try:
                rule = json.loads(rule_json)
            except ValueError:
                raise ImportError_(f'rules #{i}: rule_json is not valid JSON')
        else:
            rule = items[2]
            rule_json = json.dumps(rule, ensure_ascii=False)
        if not isinstance(rule, dict):
            raise ImportError_(f'rules #{i}: rule_json must be a JSON object')

        rules.append((i, cupt_code, codes, rule_json))
    return rules


def same_json(a, b):
    try:
        return json.loads(a) == json.loads(b)
    except ValueError:
        return False


def import_additional_projects(projects):
    counter = {'created': 0, 'updated': 0, 'unchanged': 0}
    for cupt_code, title in projects:
        custom_project = CuptExportCustomProject.objects.filter(cupt_code=cupt_code).first()
        if not custom_project:
            custom_project = CuptExportCustomProject(cupt_code=cupt_code)
            status = 'created'
        elif custom_project.title != title:
            status = 'updated'
        else:
            status = 'unchanged'

        if status != 'unchanged':
            custom_project.title = title
            custom_project.save()
            print(f'project {status}: {cupt_code} {title}')
        counter[status] += 1
    return counter


def import_rules(admission_project, rules):
    counter = {'created': 0, 'updated': 0, 'unchanged': 0}

    existing_rules = {}
    for r in (CuptExportAdditionalProjectRule.objects
              .filter(admission_project=admission_project)
              .select_related('custom_project')
              .order_by('id')):
        key = (r.custom_project_id, frozenset(split_codes(r.program_major_codes)))
        existing_rules.setdefault(key, []).append(r)
    matched_keys = set()

    for i, cupt_code, codes, rule_json in rules:
        custom_project = CuptExportCustomProject.objects.filter(cupt_code=cupt_code).first()
        if not custom_project:
            raise ImportError_(f'rules #{i}: custom project {cupt_code} not found')

        program_major_codes = ','.join(codes)
        key = (custom_project.id, frozenset(codes))
        old_rules = existing_rules.get(key, [])
        matched_keys.add(key)

        if len(old_rules) > 1:
            print(f'WARNING: rules #{i}: {len(old_rules)} existing rules match '
                  f'{cupt_code} {program_major_codes}; only the first is updated')

        if len(old_rules) == 0:
            rule = CuptExportAdditionalProjectRule(admission_project=admission_project,
                                                   custom_project=custom_project,
                                                   program_major_codes=program_major_codes)
            existing_rules[key] = [rule]
            status = 'created'
        else:
            rule = old_rules[0]
            status = 'unchanged' if same_json(rule.rule_json, rule_json) else 'updated'

        if status != 'unchanged':
            rule.rule_json = rule_json
            rule.save()
            print(f'rule {status}: {cupt_code} {rule.program_major_codes} {rule_json}')
        counter[status] += 1

    unmatched_rules = [r
                       for key, old_rules in existing_rules.items()
                       if key not in matched_keys
                       for r in old_rules]
    return counter, unmatched_rules


def main():
    parser = argparse.ArgumentParser(
        description='Import CUPT export custom projects and additional project rules')
    parser.add_argument('project_id', type=int)
    parser.add_argument('json_file')
    parser.add_argument('--dry-run', action='store_true',
                        help='report what would be created/updated without saving')
    args = parser.parse_args()

    admission_project = AdmissionProject.objects.filter(pk=args.project_id).first()
    if not admission_project:
        sys.exit(f'ERROR: admission project {args.project_id} not found')

    with open(args.json_file, encoding='utf-8') as f:
        config = json.load(f)

    print(f'Admission project: {admission_project.id} {admission_project.title}')
    if args.dry_run:
        print('DRY RUN: nothing will be saved')

    try:
        projects = parse_additional_projects(config)
        rules = parse_rules(config)

        with transaction.atomic():
            project_counter = import_additional_projects(projects)
            rule_counter, unmatched_rules = import_rules(admission_project, rules)
            if args.dry_run:
                transaction.set_rollback(True)
    except ImportError_ as e:
        sys.exit(f'ERROR: {e} (nothing imported)')

    if unmatched_rules:
        print('Existing rules of this project not in the file (left untouched):')
        for r in unmatched_rules:
            print(f'  id={r.id} {r.custom_project.cupt_code} {r.program_major_codes} {r.rule_json}')

    for name, counter in [('Custom projects', project_counter), ('Rules', rule_counter)]:
        print(f'{name}: {counter["created"]} created, {counter["updated"]} updated, '
              f'{counter["unchanged"]} unchanged')


if __name__ == '__main__':
    main()
