from django_bootstrap import bootstrap  # noqa

bootstrap()  # noqa

import sys

import xlrd
from criteria.models import MajorCuptCode, CurriculumMajor
from appl.models import AdmissionProject


def main():
    admission_projects = AdmissionProject.objects.all()
    major_cupt_codes = MajorCuptCode.objects.all()

    for ap in admission_projects:
        for cc in major_cupt_codes:
            curriculum_major = CurriculumMajor(
                admission_project=ap, cupt_code=cc, faculty=cc.faculty)
            curriculum_major.save()


if __name__ == "__main__":
    main()
