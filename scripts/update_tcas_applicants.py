from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from regis.models import Applicant

def main():
    applicant_filename = sys.argv[1]

    counter = 0
    with open(applicant_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0]

            try:
                a = Applicant.objects.get(national_id=nat_id)
            except:
                print('not found', nat_id)
                continue

            a.national_id = 'T' + items[1]
            a.prefix = items[2].strip()
            a.first_name = items[3].strip()
            a.last_name = items[4].strip()
            a.save()
            
            counter += 1

    print('Updated',counter,'applicants')
        

if __name__ == '__main__':
    main()
    
