from django_bootstrap import bootstrap
bootstrap()

import sys
import json
import csv

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionRound, AdmissionProjectRound, ProjectApplication, AdmissionResult

def get_admission_result(application,
                         admission_project,
                         admission_round,
                         major):
    results = AdmissionResult.objects.filter(application=application,
                                             admission_project=admission_project,
                                             admission_round=admission_round,
                                             major=major).all()
    if len(results) == 0:
        return None
    else:
        return results[0]

def main():
    csv_filename = sys.argv[1]
    round_id = sys.argv[2]

    admission_round = AdmissionRound.objects.get(pk=round_id)

    APPLICANT_STATUS_ACCEPTED = 2
    
    with open(csv_filename) as csvf:
        reader = csv.reader(csvf)
        next(reader)
        for items in reader:
            national_id = items[5]
            result = int(items[15])
            if result == APPLICANT_STATUS_ACCEPTED:
                applicant = Applicant.find_by_national_id(national_id)
                if applicant == None:
                    applicant = Applicant.find_by_passport_number(national_id)

                if applicant == None:
                    print('ERROR applicant not found', national_id)
                    continue

                results = AdmissionResult.objects.filter(applicant=applicant, admission_round=admission_round, is_accepted=True)
                if len(results) != 1:
                    print('ERROR results', national_id, len(results))


if __name__ == '__main__':
    main()
    
