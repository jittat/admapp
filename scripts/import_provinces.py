from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Province

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 2:
                continue

            pid = int(items[0])

            try:
                old_province = Province.objects.get(pk=pid)
                old_province.delete()
            except:
                pass

            province = Province(id=pid,
                                title=items[1])
            province.save()
            counter += 1

    print('Imported',counter,'provinces')
        

if __name__ == '__main__':
    main()
    
