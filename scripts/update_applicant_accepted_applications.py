from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, Major


def main():
    round_id = sys.argv[1]

    admission_round = AdmissionRound.objects.get(pk=round_id)
    projects = admission_round.admissionproject_set.all()

    for project in projects:
        admission_results = AdmissionResult.objects.filter(admission_project=project,
                                                           is_accepted=True).all()

        count = 0
        for res in admission_results:
            applicant = res.applicant
            application = res.application
            applicant.accepted_application = application
            applicant.save()
            count += 1

        print(project, count)
            
if __name__ == '__main__':
    main()
