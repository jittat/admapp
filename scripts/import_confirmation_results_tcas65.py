from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication, Major
from backoffice.models import MajorInterviewCallDecision

from backoffice.views.projects import load_major_applicants
from backoffice.views.projects import load_check_marks_and_results
from backoffice.views.projects import sort_applicants_by_calculated_scores
from backoffice.views.projects import update_interview_call_status


def main():
    round_id = int(sys.argv[1])
    admission_round = AdmissionRound.objects.get(pk=round_id)

    result_filename = sys.argv[2]

    is_fake = len(sys.argv) <= 3 or (sys.argv[3] != 'real')

    counter = 0
    with open(result_filename, encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row['university_id'] == '':
                continue

            
            nat_id = row['citizen_id']
            passport = row['citizen_id']
            decision = row['tcas_status']
            program_id = row['program_id']

            try:
                if nat_id != '0':
                    applicant = Applicant.objects.get(national_id=nat_id)
                else:
                    applicant = Applicant.objects.get(passport_number=passport)
            except:
                applicant = None
                
            if not applicant:
                #print('Applicant not found', nat_id, passport, row['first_name_th'])
                continue
            
            admission_results = AdmissionResult.objects.filter(applicant=applicant).all()
            accepted_results = [res for res in admission_results if res.is_accepted and res.admission_round_id == round_id]

            if len(accepted_results) != 1:
                if len(accepted_results) != 0:
                    print('ERROR accepted results', accepted_results)
                continue

            admission_result = accepted_results[0]
            application = admission_result.application

            if decision == '3':
                admission_result.has_confirmed = True
                if not is_fake:
                    admission_result.save()
                    applicant.confirmed_application = application
                    applicant.save()
            else:
                pass
                #admission_result.has_confirmed = False
                #if not is_fake:
                #    admission_result.save()
                #    try:
                #        if applicant.confirmed_application != None:
                #            applicant.confirmed_application = None
                #            applicant.save()
                #    except:
                #        print('error clearing confirmed app')

            counter += 1
            if decision == '3':
                print(counter, decision, admission_result.has_confirmed, applicant)
            
            if counter % 1000 == 0:
                print(counter)

            
if __name__ == '__main__':
    main()
