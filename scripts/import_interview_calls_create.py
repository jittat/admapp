from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    result_filename = sys.argv[1]
    project_id = sys.argv[2]
    round_id = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    all_applications = {}

    for application in (ProjectApplication.objects.filter(admission_project=admission_project,
                                                          admission_round=admission_round)
                        .select_related('applicant')
                        .select_related('major_selection')
                        .all()):
        all_applications[application.applicant.national_id] = application

    counter = 0
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0]
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue
            
            application = all_applications[nat_id]
            major_selection = application.major_selection
            
            majors = major_selection.get_majors()
            result_nums = items[1:]
            if len(majors) != len(result_nums):
                print('ERROR')

            for i in range(len(result_nums)):
                result = AdmissionResult(applicant=application.applicant,
                                         application=application,
                                         admission_project=admission_project,
                                         admission_round=admission_round,
                                         major_rank=i+1,
                                         major=majors[i])
                if result_nums[i] == '-1':
                    result.is_accepted_for_interview = False
                else:
                    result.is_accepted_for_interview = True
                    if majors[i].number != int(result_nums[i]):
                        print('ERROR - number')
                    
                result.updated_accepted_for_interview_at = datetime.now()
                result.save()
                counter += 1
            print(application.applicant)

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
