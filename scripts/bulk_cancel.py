from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from regis.models import LogItem
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
            nat_id = items[0]
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue

            application = all_applications[nat_id]
            application.is_canceled = True
            application.save()
            
            LogItem.create('Bulk cancel project {0}/{1}'.format(admission_project.id, admission_round.id),
                           application.applicant)
            counter += 1
            print(application.applicant)

        print(counter,'updated')


if __name__ == '__main__':
    main()
    
