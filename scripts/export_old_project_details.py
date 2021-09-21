from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import AdmissionProject, AdmissionProjectRound, AdmissionRound, Faculty

FIELDS = ['id','round','title','applying_warning','descriptions']

def main():
    round_id = sys.argv[1]
    csv_filename = sys.argv[2]

    admission_round = AdmissionRound.objects.get(pk=round_id)
    rows = []
    for project_round in AdmissionProjectRound.objects.filter(admission_round=admission_round):
        project = project_round.admission_project
        print(project)

        row = {
            'id': project.id,
            'round': round_id,
            'title': project.title,
            'applying_warning': project.applying_confirmation_warning,
            'descriptions': project.descriptions,
        }
        rows.append(row)

    with open(csv_filename,'w') as f:
        writer = csv.DictWriter(f, FIELDS)

        writer.writeheader()
        for r in rows:
            writer.writerow(r)
                                
        
if __name__ == '__main__':
    main()
