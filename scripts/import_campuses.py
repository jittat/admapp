from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Campus

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) != 3:
                continue
        
            campus_id = int(items[0])
            title = items[1]
            short_title = items[2]

            campus = Campus(id=campus_id,
                            title=title,
                            short_title=short_title)
            campus.save()

            counter += 1

    print('Imported',counter,'campuses')
        

if __name__ == '__main__':
    main()
    
