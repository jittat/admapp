from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Major

def main():
    filename = sys.argv[1]
    counter = 0
    
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        lines = [l for l in reader]

        for items in lines:
            
            if len(items) < 4:
                continue
            if items[0] == '':
                continue

            project_id = int(items[1])
            number = int(items[2])

            majors = Major.objects.filter(admission_project_id=project_id,
                                          number=number).all()
            if len(majors)!=1:
                print('ERROR: major error', project_id, number, majors)
                continue

            major = majors[0]
            major.slots = int(items[6])
            major.save()

            print(f'{major.admission_project} - {major.number} {major}')
            counter += 1

    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
