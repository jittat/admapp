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
            nat_id = items[0]
            if nat_id not in all_applications:
                print('ERROR', nat_id)
                continue
            
            application = all_applications[nat_id]
            results = application.admissionresult_set.all()
            if len(results) > 1:
                print('ERROR too many results', nat_id, len(results))
                continue

            if len(results) == 1:
                result = results[0]
            else:
                try:
                    majors = application.major_selection.get_majors()
                except:
                    print('ERROR', application.applicant)
                    continue
                if len(majors)!=1:
                    print('ERROR too many majors', nat_id)
                    continue
                if majors[0].number != int(items[1]):
                    print('ERROR wrong majors',nat_id, items[1])
                    continue
                result = AdmissionResult(applicant=application.applicant,
                                         application=application,
                                         admission_project=admission_project,
                                         admission_round=admission_round,
                                         major_rank=1,
                                         major=majors[0])

            result.calculated_score = float(items[2])
            result.save()
            
            print(application.applicant)
            counter += 1

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
