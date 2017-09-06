from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Campus, Faculty

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 3:
                continue
        
            title = items[1]
            campus_id = int(items[2])
            campus = Campus.objects.get(pk=campus_id)

            faculty = Faculty(title=title, campus=campus)
            faculty.save()
            counter += 1

    print('Imported',counter,'faculties')
        

if __name__ == '__main__':
    main()
    
