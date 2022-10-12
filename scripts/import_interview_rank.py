from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

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
            if (len(items) < 2) or (items[1].strip() == ''):
                continue
            nat_id = items[1]
            rank = int(items[0])

            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue
            
            application = all_applications[nat_id]

            results = AdmissionResult.find_by_application(application)
            for r in results:
                if r.is_accepted_for_interview:
                    r.interview_rank = rank
                    r.save()

            counter += 1
            
            print(application.applicant)

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
