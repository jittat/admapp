from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, Major, ProjectApplication


def main():
    round_id = sys.argv[1]

    admission_round = AdmissionRound.objects.get(pk=round_id)
    projects = admission_round.admissionproject_set.all()

    for project in projects:        
        project_applications = ProjectApplication.find_for_project_and_round(project,
                                                                             admission_round,
                                                                             True)

        count = 0
        for app in project_applications:
            if app.has_paid():
                applicant = app.applicant
                if applicant.accepted_application != None:
                    if applicant.accepted_application_id != app.id:
                        print('ERROR', applicant)
                    continue
                applicant.accepted_application = app
                applicant.save()
                count += 1

        print(project, count)
            
if __name__ == '__main__':
    main()
