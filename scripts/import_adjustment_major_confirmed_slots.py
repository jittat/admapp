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
        next(reader)
        for items in reader:
            if len(items) == 0:
                continue
            cupt_id = items[0].strip()
            if cupt_id not in confirmed_count:
                confirmed_count[cupt_id] = 0
            confirmed_count[cupt_id] += 1

    for cupt_id in confirmed_count.keys():
        #print(cupt_id)
        try:
            slot = AdjustmentMajorSlot.objects.get(cupt_code=cupt_id)
        except:
            slot = None

        if slot != None:
            slot.confirmed_slots = confirmed_count[cupt_id]
            slot.save()
        else:
            print('ERROR', cupt_id, confirmed_count[cupt_id])

        #print(confirmed_count[cupt_id], slot)
        

if __name__ == '__main__':
    main()
    
