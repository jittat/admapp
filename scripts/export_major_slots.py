from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    rows = []

    for m in project.major_set.all():
        rows.append([m.number, m.faculty.title, m.title, m.slots])

    for r in rows:
        print(','.join([str(x) for x in r]))

if __name__ == '__main__':
    main()
    
