from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Province, School

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 3:
                continue

            code = items[0].strip()
            title = items[1].strip()
            province_title = items[2].strip()

            try:
                old_school = School.objects.get(code=code)
                old_school.delete()
            except:
                pass

            try:
                province = Province.objects.get(title=province_title)
            
                school = School(title=title,
                                code=code,
                                province=province)
                school.save()
                counter += 1
            except:
                print('ERROR: Province error', code, province_title)
            

    print('Imported',counter,'schools')
        

if __name__ == '__main__':
    main()
    
