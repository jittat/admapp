from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import School
from supplements.models import TopSchool

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            code = items[3].strip()
            school = School.objects.get(code=code)
            try:
                old_topschool = TopSchool.objects.get(school=school)
                old_topschool.delete()
            except:
                pass
            topschool = TopSchool(school=school)
            topschool.save()
            counter += 1

    print('Imported',counter,'top schools')
        

if __name__ == '__main__':
    main()
    
