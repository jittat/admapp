from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Campus, AdmissionRound, AdmissionProject, AdmissionProjectRound

def extract_datetime(date_str, time_str):
    from datetime import datetime
    return datetime.strptime(date_str.strip() + ' ' + time_str.strip(),
                             '%Y-%m-%d %H:%M:%S')

def main():
    admission_rounds = dict([(r.id,r) for r in AdmissionRound.objects.all()])
    
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        
        for items in reader:
            pid = int(items[0])
            round_number = int(items[1])
            title = items[2].strip()
            warning = items[8]
            start_date = items[3].strip()
            start_time = items[4].strip()
            end_date = items[5].strip()
            end_time = items[6].strip()
            last_payment_date = items[7].strip()

            project = AdmissionProject.objects.get(pk=pid)
            admission_round = AdmissionRound.objects.get(number=round_number)
            project_round = project.get_project_round_for(admission_round)

            if project.title != title:
                print('ERROR Title mismatch', title, project.title)
                continue

            project_round.applying_start_time = extract_datetime(start_date, start_time)
            project_round.applying_deadline = extract_datetime(end_date, end_time)
            project_round.payment_deadline = extract_datetime(last_payment_date,'00:00:00').date()
            project_round.save()
            
            if warning != '':
                project.applying_confirmation_warning = warning
                project.save()

            print('Imported:', project)
            counter += 1

    print('Imported',counter,'projects')
        

if __name__ == '__main__':
    main()
    
