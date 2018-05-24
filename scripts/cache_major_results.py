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

    for application in applications:
        a = application.applicant
        major_selection = application.get_major_selection()
        majors = major_selection.get_majors()

        old = ApplicantMajorResult.objects.filter(applicant=a,
                                                  admission_project=project).all()
        for mr in old:
            mr.delete()
        
        for m in majors:
            major_results = ApplicantMajorResult.objects.filter(applicant=a,
                                                                major=m,
                                                                admission_project=project).all()
            major_result = ApplicantMajorResult()
            major_result.applicant = a
            major_result.project_application = application
            major_result.major = m
            major_result.admission_project = project
            major_result.save()
                
            
            old_scores = ApplicantMajorScore.objects.filter(major=m,
                                                            admission_project=project,
                                                            applicant=a)
            for oscore in old_scores:
                oscore.delete()
        
            for ex in a.examscore_set.all():
                ascore = ApplicantMajorScore()
                ascore.applicant = a
                ascore.major = m
                ascore.admission_project = project
                ascore.exam_score = ex
                ascore.save()
            
            
        print(a.national_id)

if __name__ == '__main__':
    main()
