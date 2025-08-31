from django_bootstrap import bootstrap
bootstrap()

from datetime import date
import sys
import csv

from appl.models import Campus, AdmissionRound, AdmissionProject


def main():
    admission_rounds = dict([(r.id,r) for r in AdmissionRound.objects.all()])

    round_dates = {
        1: (date(2025,12,7), date(2025,12,8)),
        5: (date(2026,1,25), date(2026,1,26)),
        2: (date(2026,4,27), date(2026,4,27)),
        3: (date(2026,5,29), date(2026,5,29)),
    }

    counter = 0

    for project in AdmissionProject.objects.all():
        admission_rounds = project.admission_rounds.all()
        if not admission_rounds:
            continue
        r = admission_rounds[0]
        if r.id in round_dates:
            project.custom_interview_start_date = round_dates[r.id][0]
            project.custom_interview_end_date = round_dates[r.id][1]
            project.is_custom_interview_date_allowed = True
            project.save()
            counter += 1
            print(project)

    print('Updated',counter,'projects')
        

if __name__ == '__main__':
    main()
    
