from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication

def main():
    gpa_filename = sys.argv[1]
    project_id = sys.argv[2]
    round_id = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    all_applications = {}

    for application in (ProjectApplication.objects.filter(admission_project=admission_project,
                                                          admission_round=admission_round,
                                                          is_canceled=False)
                        .select_related('applicant')
                        .select_related('major_selection')
                        .all()):
        all_applications[application.applicant.national_id] = application

    counter = 0
    with open(gpa_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) != 2:
                continue
            nat_id = items[0]
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue

            application = all_applications[nat_id]
            applicant = application.applicant
            edu = applicant.educationalprofile
            if edu.gpa != float(items[1]):
                edu.gpa = float(items[1])
                edu.save()
                counter += 1
                print(applicant, edu.gpa)

        print(counter,'updated')


if __name__ == '__main__':
    main()
    
