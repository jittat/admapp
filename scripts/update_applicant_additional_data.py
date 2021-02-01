from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant

def main():
    fname = sys.argv[1]

    lines = open(fname).readlines()

    counter = 0
    for l in lines:
        items = l.split(";")
        if len(items) != 2:
            continue
        
        a = Applicant.objects.get(national_id=items[0])
        a.additional_data = items[1]
        a.save()
        counter += 1
        
    print(counter,'updated')
            
if __name__ == '__main__':
    main()
