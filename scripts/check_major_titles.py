from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound, AdmissionProjectRound, Major

def full_name(major):
    return f'{major.faculty} {major.title}'

def main():
    r = int(sys.argv[1])

    for project_round in AdmissionProjectRound.objects.filter(admission_round_id=r):
        project = project_round.admission_project

        titles = set()
        count = 0
        for m in project.major_set.all():
            if full_name(m) in titles:
                print('>>> ERROR', project, full_name(m))
            titles.add(full_name(m))
            count += 1
        if count != 0:
            print(f'{project} ({project.id}) - {count} สาขา')

if __name__ == '__main__':
    main()

