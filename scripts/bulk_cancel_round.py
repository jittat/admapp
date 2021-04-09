from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    cancel_filename = sys.argv[1]
    round_id = sys.argv[2]

    admission_round = AdmissionRound.objects.get(pk=round_id)

    all_applications = {}

    for project_round in admission_round.admissionprojectround_set.all():
        admission_project = project_round.admission_project

        for application in (ProjectApplication.objects.filter(admission_project=admission_project,
                                                              admission_round=admission_round,
                                                              is_canceled=False)
                            .select_related('applicant')
                            .select_related('major_selection')
                            .all()):
            all_applications[application.applicant.national_id] = application

    counter = 0
    with open(cancel_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0]
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue

            application = all_applications[nat_id]

            application.is_canceled = True
            application.save()

            LogItem.create('Bulk cancel project {0}/{1}'.format(application.admission_project.id,
                                                                admission_round.id),
                           application.applicant)
            
            counter += 1

            if application.has_paid():
                print('[PAID] ', application.applicant, application.admission_project)
            else:
                print(application.applicant, application.admission_project)

    print(counter,'updated')


if __name__ == '__main__':
    main()
    
