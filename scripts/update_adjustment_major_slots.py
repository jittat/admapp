from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import AdmissionRound
from backoffice.models import AdjustmentMajor, AdjustmentMajorSlot

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            major_full_code = items[0].strip()
            updated_num = int(items[1].strip())

            if updated_num == 0:
                continue

            try:
                slot = AdjustmentMajorSlot.objects.get(cupt_code=major_full_code)
            except:
                slot = None

            if not slot:
                print('ERROR major not found', slot, items)
                continue

            print(slot, 'updated:', updated_num, 'from:', slot.current_slots)
            
            slot.current_slots += updated_num
            slot.save()
            
            counter += 1

    print('Imported',counter,'slots')
        

if __name__ == '__main__':
    main()
    
