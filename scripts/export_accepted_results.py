from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    round_id = sys.argv[1]

    admission_round = AdmissionRound.objects.get(pk=round_id)

    results = AdmissionResult.objects.filter(is_accepted_for_interview=True, admission_round=admission_round).all()

    for r in results:
        national_id = r.applicant.national_id
        project_id = r.admission_project_id
        score = r.calculated_score
        major = r.major
        major_number = r.major.number
        
        print(','.join([national_id, str(major_number), str(project_id), str(score)]))


if __name__ == '__main__':
    main()
    
