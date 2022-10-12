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
        first = True
        for items in reader:
            if first:
                first = False
                continue

            full_major_project_code = items[0].strip()
            major_full_code = items[6].strip()
            project_title = items[1].strip()
            round_number = int(items[4])

            try:
                adj_major = AdjustmentMajor.objects.get(full_code=major_full_code)
            except:
                adj_major = None

            if not adj_major:
                print('ERROR major not found', major_full_code, items)
                continue
            
            old_slots = AdjustmentMajorSlot.objects.filter(adjustment_major=adj_major).all()
            slot = None
            for s in old_slots:
                if s.cupt_code == full_major_project_code:
                    slot = s
            if not slot:
                slot = AdjustmentMajorSlot()

            slot.adjustment_major = adj_major
            slot.faculty = adj_major.faculty
            slot.admission_round = AdmissionRound.objects.get(pk=round_number)
            slot.admission_round_number = round_number
            slot.major_full_code = major_full_code
            slot.cupt_code = full_major_project_code
            slot.admission_project_title = project_title

            if items[5] != '':
                slot.original_slots = int(items[5])
            else:
                slot.original_slots = 0
                
            slot.current_slots = slot.original_slots
            
            slot.save()
            
            print(slot)
            
            counter += 1

    print('Imported',counter,'slots')
        

if __name__ == '__main__':
    main()
    
