from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication, AdmissionProjectRound

def read_confirmed_applicants(filename):
    return [st.strip().split(',') for st in open(filename).readlines()[1:]]

def main():
    round_id = sys.argv[1]
    filename = sys.argv[2]

    admission_round = AdmissionRound.objects.get(pk=round_id)

    confirmed_applicants = read_confirmed_applicants(filename)

    accepted_results = []

    for project_round in AdmissionProjectRound.objects.filter(admission_round=admission_round).all():
        project = project_round.admission_project
        print(project)
        accepted_results += (AdmissionResult.objects.filter(admission_project=project,
                                                            admission_round=admission_round,
                                                            is_accepted=True).all())

    accepted_applications = dict([((str(r.application.get_number()), r.application.applicant_id),
                                   (r.application,r)) for r in accepted_results])

    counter = 0
    
    for (nat_id, cupt_major_number, number) in confirmed_applicants:
        number = number.strip()
        nat_id = nat_id.strip()
        applicant = Applicant.find_by_national_id(nat_id)
        if not applicant:
            applicant = Applicant.find_by_passport_number(nat_id)

        if not applicant:
            print('ERROR1 ' + number + ' ' + nat_id)
            continue
        
        if (number, applicant.id) not in accepted_applications:
            print('ERROR2 ' + number + ' ' + str(applicant.id))
            continue

        application = accepted_applications[(number, applicant.id)][0]
        result = accepted_applications[(number, applicant.id)][1]

        if result.major.get_full_major_cupt_code() != cupt_major_number:
            print('ERROR3 ' + number + ' ' + str(applicant.id) + ' ' + cupt_major_number)
            continue
        
        applicant = application.applicant
        applicant.confirmed_application = application
        applicant.save()

        result.has_confirmed = True
        result.save()
        
        #print(applicant)

        counter += 1

    print(counter, 'saved')

if __name__=='__main__':
    main()
