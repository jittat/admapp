from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication
from admapp.emails import send_clearing_house_email

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    all_results = AdmissionResult.objects.filter(admission_project=admission_project,
                                             admission_round=admission_round).all()
    
    results = [x[2] for x in sorted([(r.major.number, r.applicant.national_id, r) for r in all_results])]

    count = 0
    for res in results:
        if res.is_accepted:
            count += 1
            applicant = res.applicant
            clearing_code = res.clearing_house_code

            if applicant.has_registered_with_passport():
                username = applicant.passport_number
            else:
                username = applicant.national_id

            send_clearing_house_email(applicant, res, clearing_code, username)

            print(applicant.get_full_name())
            
if __name__ == '__main__':
    main()
    
