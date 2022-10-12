from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication


def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    is_fake = len(sys.argv) <= 3 or (sys.argv[3] != 'real')

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    applications = ProjectApplication.objects.filter(admission_project=admission_project,
                                                   admission_round=admission_round,
                                                   is_canceled=False).all()

    counter = 0
    for application in applications:
        applicant = application.applicant
        admission_results = AdmissionResult.objects.filter(applicant=applicant).all()
        accepted_results = [res for res in admission_results if res.is_accepted]

        if len(accepted_results) != 1:
            continue

        admission_result = accepted_results[0]
        application = admission_result.application

        applicant.confirmed_application = application

        if not is_fake:
            applicant.save()

        counter += 1
        print(counter, admission_result.has_confirmed, applicant)
            
        if counter % 1000 == 0:
            print(counter)

    print(counter,'updated')
            
if __name__ == '__main__':
    main()
