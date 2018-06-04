from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication
from backoffice.models import MajorInterviewCallDecision

def main():
    project_id = sys.argv[1]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    results = AdmissionResult.objects.filter(admission_project=admission_project).all()

    count = 0
    for r in results:
        r.is_tcas_result = True
        if r.is_accepted_for_interview:
            r.tcas_acceptance_round_number = 1
        r.save()

        count += 1
        if count % 1000 == 0:
            print(count)
        

if __name__ == '__main__':
    main()
    
