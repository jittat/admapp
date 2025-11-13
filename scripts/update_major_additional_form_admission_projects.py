from django_bootstrap import bootstrap
bootstrap()
import sys

from appl.models import Major, AdmissionRound, AdmissionProject, AdmissionProjectRound
from appl.models import MajorAdditionalNotice, MajorAdditionalAdmissionFormField
from criteria.models import MajorCuptCode

def main():
    count = 0

    for f in MajorAdditionalAdmissionFormField.objects.all():
        major = f.major
        if f.admission_project_id == None:
            f.admission_project = major.admission_project
            f.save()
            count += 1

    print('Updated', count, 'majors')


if __name__ == '__main__':
    main()
