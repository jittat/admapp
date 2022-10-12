from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionResult, AdmissionRound


def read_applicant_numbers(filename):
    return [int(st.strip()) for st in open(filename).readlines()]

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]
    filename = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    confirmed_applicant_numbers = read_applicant_numbers(filename)

    accepted_results = AdmissionResult.objects.filter(admission_project=admission_project,
                                                      admission_round=admission_round,
                                                      is_accepted=True).all()

    accepted_applications = dict([(r.application.get_number(),r.application) for r in accepted_results])

    for number in confirmed_applicant_numbers:
        if number not in accepted_applications:
            print('ERROR ' + number)
            continue

        application = accepted_applications[number]
        applicant = application.applicant
        applicant.confirmed_application = application
        applicant.save()

        results = application.admissionresult_set.all()
        if len(results) != 1:
            print('ERROR result')
            continue
        result = results[0]
        result.has_confirmed = True
        result.save()
        
        print(applicant)

if __name__=='__main__':
    main()
