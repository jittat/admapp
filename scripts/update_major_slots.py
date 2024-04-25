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
            if items[0].strip() == '':
                continue

            try:
                project_id = int(items[0])
            except:
                project_id = 0

            if project_id == 0:
                continue
            
            cupt_full_code = items[3]

            majors = Major.objects.filter(admission_project_id=project_id,
                                          cupt_full_code=cupt_full_code).all()
            if len(majors)!=1:
                print('ERROR: major error', project_id, cupt_full_code, majors)
                continue

            major = majors[0]
            old_slot = major.slots
            if old_slot != int(items[6]):
                print('mismatch:', major, old_slot, items[6])
            new_slot = int(items[7])
            major.slots = int(items[7])
            #if major.title != items[5].strip():
            #    print('ERROR not match', major.title, items[5])
            #major.save()

            print(f'{major.admission_project} - {major.number} {major} - {old_slot} - {new_slot}')
            counter += 1

    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
