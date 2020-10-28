from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from criteria.models import AdmissionCriteria

def main():
    csv_filename = sys.argv[1]
    with open(csv_filename) as csv_file:
        for l in csv_file.readlines():
            items = l.strip().split(',')

            if len(items) != 3:
                continue

            id = items[0]
            c = AdmissionCriteria.objects.get(pk=id)
            c.additional_description = items[1].strip()
            c.additional_condition = items[2].strip()
            c.save()
            
            print(items[0], l.strip())

if __name__ == '__main__':
    main()
