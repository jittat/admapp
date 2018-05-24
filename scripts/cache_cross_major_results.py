from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from random import choice
from datetime import datetime

from regis.models import Applicant
from appl.models import Major, MajorSelection, ProjectApplication, AdmissionProjectRound, EducationalProfile
from backoffice.models import ApplicantMajorResult, ApplicantMajorScore

def main():
    project_round_id = sys.argv[1]

    project_round = AdmissionProjectRound.objects.get(pk=project_round_id)
    project = project_round.admission_project
    admission_round = project_round.admission_round

    applications = ProjectApplication.find_for_project_and_round(project,
                                                                 admission_round,
                                                                 True)
    majors = dict([(m.number, m) for m in
                   Major.objects.filter(admission_project=project).all()])

    counter = 0
    
    for application in applications:
        a = application.applicant
        major_selection = application.get_major_selection()
        majors = major_selection.get_majors()

        old = ApplicantMajorResult.objects.filter(applicant=a,
                                                  admission_project=project).all()

        results = {}

        if len(majors) < 2:
            continue
        
        for m in majors:
            major_result = (ApplicantMajorResult
                            .objects
                            .filter(applicant=a,
                                    major=m,
                                    admission_project=project)
                            .select_related('admission_result')
                            .all()[0])
            
            results[m.number] = major_result

        for m in majors:
            result = results[m.number]

            other_scores =  []
            for mm in result.get_other_major_numbers():
                other_scores.append(results[mm].admission_result.calculated_score)

            result.other_major_scores = ','.join([('%5f' % sc) for sc in other_scores])

            result.save()
            
        counter += 1
        if counter % 1000 == 0:
            print(counter, a.national_id)

if __name__ == '__main__':
    main()
