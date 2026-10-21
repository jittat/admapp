from django_bootstrap import bootstrap
bootstrap()

import argparse
import csv
from datetime import datetime

from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

# Calls each applicant listed in the CSV for interview on *all* majors they
# applied to, and clears interview calls of applicants not in the CSV.
# CSV layout is the same as import_interview_calls_culture.py
# (national id in column 1; other columns are ignored).

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('result_filename')
    parser.add_argument('project_id')
    parser.add_argument('round_id')
    parser.add_argument('--dry-run', action='store_true',
                        help='print changes without saving')
    args = parser.parse_args()
    dry_run = args.dry_run

    admission_project = AdmissionProject.objects.get(pk=args.project_id)
    admission_round = AdmissionRound.objects.get(pk=args.round_id)

    all_applications = {}

    for application in (ProjectApplication.objects.filter(admission_project=admission_project,
                                                          admission_round=admission_round,
                                                          is_canceled=False)
                        .select_related('applicant')
                        .select_related('major_selection')
                        .all()):
        all_applications[application.applicant.national_id] = application

    called_applications = set()
    now = datetime.now()

    counter = 0
    with open(args.result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 2:
                continue
            nat_id = items[1].strip()
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue

            application = all_applications[nat_id]
            if application.id in called_applications:
                continue

            try:
                major_selection = application.major_selection
            except Exception:
                major_selection = None
            if major_selection is None:
                print('ERROR no major selection', nat_id)
                continue

            majors = major_selection.get_majors()

            for i in range(len(majors)):
                old_results = AdmissionResult.objects.filter(application=application,
                                                             admission_project=admission_project,
                                                             admission_round=admission_round,
                                                             major=majors[i]).all()
                if len(old_results) > 0:
                    result = old_results[0]
                else:
                    result = AdmissionResult(applicant=application.applicant,
                                             application=application,
                                             admission_project=admission_project,
                                             admission_round=admission_round,
                                             major_rank=i+1,
                                             major=majors[i])

                result.is_accepted_for_interview = True
                result.updated_accepted_for_interview_at = now
                if not dry_run:
                    result.save()
                counter += 1
            print(application.applicant, [m.title for m in majors])

            called_applications.add(application.id)

    cleared = 0
    for app in all_applications.values():
        if app.id not in called_applications:
            old_results = AdmissionResult.objects.filter(application=app,
                                                         admission_project=admission_project,
                                                         admission_round=admission_round).all()
            for res in old_results:
                if res.is_accepted_for_interview:
                    res.is_accepted_for_interview = False
                    res.updated_accepted_for_interview_at = now
                    if not dry_run:
                        res.save()
                    cleared += 1
                    print('cleared', res.id, app.applicant.national_id)

    prefix = '[DRY RUN] ' if dry_run else ''
    print(f'{prefix}Called {len(called_applications)} applicants, set {counter} results, cleared {cleared} results')


if __name__ == '__main__':
    main()
