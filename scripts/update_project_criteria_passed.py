from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult


def main():
    result_filename = sys.argv[1]
    project_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    all_applications = {}

    counter = 0
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0]
            applicant = Applicant.objects.get(national_id=nat_id)
            results = AdmissionResult.objects.filter(applicant=applicant, admission_project=admission_project).all()
            if len(results) != 1:
                print('ERROR', nat_id, 'num results =', len(results))
                continue
            
            result = results[0]
            result.is_criteria_passed = True
            result.updated_criteria_passed_at = datetime.now()
            result.save()
            counter += 1
            print(applicant)

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
