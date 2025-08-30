from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionResult, AdmissionRound
from criteria.models import AdmissionCriteria, CurriculumMajorAdmissionCriteria

def main():
    for criteria in AdmissionCriteria.objects.filter(is_deleted=False):
        criteria.is_from_last_year = True
        cmas = criteria.curriculummajoradmissioncriteria_set.all()
        majors = []
        for cma in cmas:
            majors.append(str(cma.curriculum_major.cupt_code))
        criteria.last_year_major_titles = ';'.join(majors)
        criteria.save()
        print(criteria.admission_project, criteria.faculty, criteria, criteria.last_year_major_titles)

if __name__ == '__main__':
    main()
