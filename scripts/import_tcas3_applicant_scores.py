from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication
from backoffice.models import ApplicantMajorResult

def main():
    result_filename = sys.argv[1]
    project_id = sys.argv[2]
    round_id = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    all_applications = {}

    for application in (ProjectApplication.objects.filter(admission_project=admission_project,
                                                          admission_round=admission_round,
                                                          is_canceled=False)
                        .select_related('applicant')
                        .select_related('major_selection')
                        .all()):
        all_applications[application.applicant.national_id] = application

    counter = 0
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            major_number = int(items[0])
            nat_id = items[1]
            score = float(items[2])
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue
            
            application = all_applications[nat_id]

            majors = [m for m in application.major_selection.get_majors()
                      if m.number == major_number]

            if len(majors) == 0:
                print('ERROR major not found', nat_id)

            major = majors[0]

            old_results = AdmissionResult.objects.filter(application=application,
                                                         major=major).all()

            if old_results:
                result = old_results[0]
            else:
                result = AdmissionResult()
                
            result.applicant=application.applicant
            result.application=application
            result.admission_project=admission_project
            result.admission_round=admission_round
            result.major_rank=1
            result.major=major
            result.calculated_score = score
            result.save()

            major_results = ApplicantMajorResult.objects.filter(major=major,
                                                                admission_project=admission_project,
                                                                applicant=application.applicant).all()

            if len(major_results) != 0:
                major_result = major_results[0]
                major_result.admission_result = result
                major_result.save()
                print('saved',major.number)
            
            print(application.applicant)
            counter += 1

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
