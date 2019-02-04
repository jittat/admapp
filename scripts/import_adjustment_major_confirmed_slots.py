from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from django.contrib.auth.models import User
from appl.models import Faculty, AdmissionRound
from backoffice.models import AdjustmentMajor, AdjustmentMajorSlot

def main():
    filename = sys.argv[1]
    counter = 0

    confirmed_count = {}
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            cupt_id = items[2].strip()
            if cupt_id not in confirmed_count:
                confirmed_count[cupt_id] = 0
            confirmed_count[cupt_id] += 1

    for cupt_id in confirmed_count.keys():
        slot = AdjustmentMajorSlot.objects.get(cupt_code=cupt_id)
        slot.confirmed_slots = confirmed_count[cupt_id]
        slot.save()

        print(slot)
        

if __name__ == '__main__':
    main()
    
