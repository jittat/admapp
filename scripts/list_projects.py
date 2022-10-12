from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionRound


def read_applicant_numbers(filename):
    return [int(st.strip()) for st in open(filename).readlines()]

def main():
    admission_round_id = sys.argv[1]
    admission_round = AdmissionRound.objects.get(pk=admission_round_id)

    projects = admission_round.admissionprojectround_set.all()
    for p in projects:
        if p.admission_project.is_available:
            print(p.admission_project.id, p.admission_project)


if __name__ == '__main__':
    main()
