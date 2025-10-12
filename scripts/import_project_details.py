from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import AdmissionRound, AdmissionProject


def extract_datetime(date_str, time_str):
    from datetime import datetime
    return datetime.strptime(date_str.strip() + ' ' + time_str.strip(),
                             '%Y-%m-%d %H:%M:%S')

def get_admission_round_number(round_number_str):
    try:
        round_number = int(round_number_str)
        admission_round = AdmissionRound.objects.get(number=round_number)
        return admission_round
    except:
        pass

    num,sub = [int(x) for x in round_number_str.split('.')]
    admission_rounds = AdmissionRound.objects.filter(number=num,subround_number=sub).all()
    if len(admission_rounds)==1:
        return admission_rounds[0]
    raise "Admission Round not found"

def main():
    admission_rounds = dict([(r.id,r) for r in AdmissionRound.objects.all()])
    
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        
        for items in reader:
            pid = int(items[0])
            round_number_str = items[1].strip()
            title = items[2].strip()
            warning = items[8]
            descriptions = items[9]
            start_date = items[3].strip()
            start_time = items[4].strip()
            end_date = items[5].strip()
            end_time = items[6].strip()
            last_payment_date = items[7].strip()

            if len(items) >= 11:
                pdf_url = items[10].strip()
            else:
                pdf_url = None

            project = AdmissionProject.objects.get(pk=pid)
            admission_round = get_admission_round_number(round_number_str)
            project_round = project.get_project_round_for(admission_round)

            if project.title != title:
                print('ERROR Title mismatch', title, project.title)
                #continue

            project_round.applying_start_time = extract_datetime(start_date, start_time)
            project_round.applying_deadline = extract_datetime(end_date, end_time)
            project_round.payment_deadline = extract_datetime(last_payment_date,'00:00:00').date()
            project_round.save()
            
            if warning != '':
                if '”' in warning:
                    warning = warning.replace('”','"')
                if (pdf_url != None) and ('PDFURL' in warning):
                    warning = warning.replace('PDFURL', pdf_url)
                project.applying_confirmation_warning = warning
                project.save()

            if descriptions != '':
                if '”' in descriptions:
                    descriptions = descriptions.replace('”','"')
                if (pdf_url != None) and ('PDFURL' in descriptions):
                    descriptions = descriptions.replace('PDFURL', pdf_url)
                project.descriptions = descriptions
                project.save()

            print('Imported:', project)
            counter += 1

    print('Imported',counter,'projects')
        

if __name__ == '__main__':
    main()
    
