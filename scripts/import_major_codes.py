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
        next(reader)
        for items in reader:
            if len(items) < 5:
                continue

            project_id = int(items[0])
            major_number = int(items[1])
            cupt_code = items[4].strip()
            cupt_study_type_code = items[5].strip()
            if (len(items) >= 7) and (items[6]!=''):
                cupt_full_code = items[6].strip()
            else:
                cupt_full_code = ''

            major = Major.objects.get(admission_project_id=project_id,
                                      number=major_number)
            major.cupt_code = cupt_code
            major.cupt_study_type_code = cupt_study_type_code
            major.cupt_full_code = cupt_full_code
            major.save()

            print(project_id, major_number)
            
            counter += 1

    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
