from django_bootstrap import bootstrap
bootstrap()

import csv
import sys

from appl.models import AdmissionProject


FIELDS = [
    'is_custom_curriculum_type_allowed',
    'is_custom_graduate_year_allowed',
    'is_custom_add_limit_criteria',

    'admission_student_type',
    'admission_school_type',

    'is_custom_score_criteria_allowed',

    'is_custom_interview_date_allowed',
    'custom_interview_start_date',
    'custom_interview_end_date',

    'is_portfolio_submission_required',
    'is_additional_admission_upload_allowed',
    'is_additional_admission_late_upload_allowed',
    'late_upload_date',

    'is_additional_admission_form_allowed',
    'is_additional_admission_form_edit_allowed',

    'is_additional_notice_allowed',

    'is_criteria_edit_allowed',
]

HEADER = ['id', 'title'] + FIELDS


def format_value(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return '1' if value else '0'
    return str(value)


def project_row(project):
    return ([str(project.id), project.title] +
            [format_value(getattr(project, f)) for f in FIELDS])


def main():
    if len(sys.argv) > 1:
        out_file = open(sys.argv[1], 'w', newline='', encoding='utf-8')
    else:
        out_file = sys.stdout

    writer = csv.writer(out_file)
    writer.writerow(HEADER)

    projects = sorted(AdmissionProject.objects.all(),
                      key=lambda p: (p.id % 100, p.id))

    for project in projects:
        writer.writerow(project_row(project))

    if out_file is not sys.stdout:
        out_file.close()


if __name__ == '__main__':
    main()
