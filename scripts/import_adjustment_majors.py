from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Faculty
from backoffice.models import AdjustmentMajor

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        first = True
        for items in reader:
            if first:
                first = False
                continue

            facid = items[0]
            full_code = items[1].strip()
            title = items[3]
            
            faculty_title = items[2]

            print(faculty_title)
            faculty = Faculty.objects.get(title=faculty_title)

            old_adj_majors = AdjustmentMajor.objects.filter(full_code=full_code).all()
            if len(old_adj_majors)!=0:
                adj_major = old_adj_majors[0]
            else:
                adj_major = AdjustmentMajor()

            adj_major.full_code = full_code
            adj_major.title = title
            adj_major.faculty = faculty
            adj_major.major_code = full_code
            adj_major.study_type_code = items[4]
            adj_major.save()

            print(adj_major, faculty, adj_major.major_code, adj_major.study_type_code)
            
            counter += 1

    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
