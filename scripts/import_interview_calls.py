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
    project_round = admission_project.get_project_round_for(admission_round)

    all_applications = {}

    for application in (ProjectApplication.objects.filter(admission_project=admission_project,
                                                          admission_round=admission_round)
                        .select_related('applicant')
                        .select_related('major_selection')
                        .all()):
        all_applications[application.applicant.national_id] = application

    counter = 0
    create_counter = 0
    change_count = 0

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
            accepted_major_number = int(items[1])

            mcount = 0
            for m in majors:
                old_result = None
                old_accepted = None
                old_results = AdmissionResult.objects.filter(applicant=application.applicant,
                                                             admission_round=admission_round,
                                                             admission_project=admission_project,
                                                             major=m).all()
                if len(old_results) != 0:
                    old_result = old_results[0]
                    result = old_result
                    if project_round.criteria_check_required:
                        if not result.is_criteria_passed:
                            print('ERROR', nat_id, 'not passed criteria')
                    old_accepted = result.is_accepted_for_interview
                else:
                    result = AdmissionResult(applicant=application.applicant,
                                             application=application,
                                             admission_project=admission_project,
                                             admission_round=admission_round,
                                             major_rank=mcount+1,
                                             major=m)
                    create_counter += 1

                if m.number == accepted_major_number:
                    result.is_accepted_for_interview = True
                    if (not old_result) and (project_round.criteria_check_required):
                        result.is_criteria_passed = True
                else:
                    result.is_accepted_for_interview = False
                    
                if (old_result) and (old_accepted != None) and (old_accepted != result.is_accepted_for_interview):
                    change_count += 1

                result.updated_accepted_for_interview_at = datetime.now()
                result.save()
                mcount += 1

                counter += 1
            print(application.applicant)

    print('Imported',counter,'results')
    print('New results created:', create_counter)
    print('Changed results:', change_count)     

if __name__ == '__main__':
    main()
