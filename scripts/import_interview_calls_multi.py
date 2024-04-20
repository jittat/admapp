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
    old_nat_id = ""
    is_first = True
    
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0]
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue
            
            application = all_applications[nat_id]
            major_selection = application.major_selection
            applicant = application.applicant

            if nat_id != old_nat_id:
                is_first = True
            else:
                is_first = False
            old_nat_id = nat_id
            
            majors = major_selection.get_majors()
            if len(items) < 2:
                print('Skip', nat_id)
                continue
            result_major_num = int(items[2])

            if is_first:
                old_results = AdmissionResult.objects.filter(applicant=application.applicant,
                                                             admission_round=admission_round,
                                                             admission_project=admission_project).all()
                if len(old_results) != 0:
                    print('ARRRGGG', nat_id)
            
            for i in range(len(majors)):
                old_results = AdmissionResult.objects.filter(applicant=application.applicant,
                                                             application=application,
                                                             admission_project=admission_project,
                                                             major=majors[i]).all()
                if len(old_results)==1:
                    result = old_results[0]
                else:
                    result = AdmissionResult(applicant=application.applicant,
                                             application=application,
                                             admission_project=admission_project,
                                             admission_round=admission_round,
                                             major_rank=i+1,
                                             major=majors[i])
                if majors[i].number == result_major_num:
                    result.is_accepted_for_interview = True
                    print(nat_id, application.applicant, majors[i])
                    result.updated_accepted_for_interview_at = datetime.now()
                    result.save()
                    counter += 1
            print(application.applicant)

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
