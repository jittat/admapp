from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, Major, ProjectApplication


def main():
    round_id = sys.argv[1]

    admission_round = AdmissionRound.objects.get(pk=round_id)
    projects = admission_round.admissionproject_set.all()

    applicants = (Applicant.objects.filter(accepted_application__isnull=False)
                           .select_related('accepted_application')
                           .all())    

    count = 0

    for applicant in applicants:
        application = applicant.accepted_application
        if application.admission_round_id == int(round_id):
            applicant.accepted_application = None
            applicant.save()
            count += 1

    print('Updated', count, 'applicants.')
            
if __name__ == '__main__':
    main()
