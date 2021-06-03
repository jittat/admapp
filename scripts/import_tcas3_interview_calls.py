from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    result_filename = sys.argv[1]
    project_id = 28
    round_id = 3

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
            if len(items) < 4:
                continue
            
            nat_id = 'x' + items[0]
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue
            
            application = all_applications[nat_id]
            major_selection = application.major_selection
            
            majors = major_selection.get_majors()
            interview_major_num  = int(items[6])

            found = False
            for i in range(len(majors)):
                old_results = AdmissionResult.objects.filter(application=application,
                                                             admission_project=admission_project,
                                                             admission_round=admission_round,
                                                             major=majors[i])

                if len(old_results) > 0:
                    result = old_results[0]
                else:
                    result = AdmissionResult(applicant=application.applicant,
                                             application=application,
                                             admission_project=admission_project,
                                             admission_round=admission_round,
                                             major_rank=i+1,
                                             major=majors[i])
                if majors[i].number != interview_major_num:
                    result.is_accepted_for_interview = False
                else:
                    found = True
                    result.is_accepted_for_interview = True
                    
                result.updated_accepted_for_interview_at = datetime.now()
                result.save()
                counter += 1
            if not found:
                print('ERROR, major not found', interview_major_num)
            print(application.applicant)

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
