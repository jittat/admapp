from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    results = AdmissionResult.objects.filter(admission_project=admission_project,
                                             admission_round=admission_round).all()

    for res in results:
        if res.is_accepted:
            items = [res.applicant.national_id,
                     res.applicant.get_full_name(),
                     str(res.major.number),
                     res.major.title]
            print(','.join(items))

if __name__ == '__main__':
    main()
    
