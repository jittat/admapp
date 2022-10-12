from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Faculty

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 5:
                continue
        
            id = items[0]
            ku_code = items[3].strip()
            cupt_code = items[4].strip()

            faculty = Faculty.objects.get(pk=id)
            faculty.ku_code = ku_code
            faculty.cupt_code =cupt_code
            faculty.save()
            counter += 1

    print('Imported',counter,'faculties')
        

if __name__ == '__main__':
    main()
    
