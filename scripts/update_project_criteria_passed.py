from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, Major, ProjectApplication


def main():
    result_filename = sys.argv[1]
    project_id = sys.argv[2]
    admission_round_id = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=admission_round_id)
    all_applications = {}

    counter = 0
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0]
            major_number = items[1]

            major = Major.objects.filter(admission_project=admission_project, number=major_number).all()[0]

            applicant = Applicant.objects.get(national_id=nat_id)
            results = AdmissionResult.objects.filter(applicant=applicant,
                                                     admission_project=admission_project,
                                                     major=major).all()
            if len(results) != 0:
                result = results[0]
            else:
                applications = ProjectApplication.objects.filter(applicant=applicant,
                                                                 admission_project=admission_project,
                                                                 is_canceled=False).all()
                application = applications[0]
                result = AdmissionResult(applicant=applicant,
                                         application=application,
                                         admission_project=admission_project,
                                         admission_round=admission_round,
                                         major_rank=1,
                                         major=major)
                
            result.is_criteria_passed = True
            result.updated_criteria_passed_at = datetime.now()
            result.save()
            counter += 1
            print(applicant)

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
