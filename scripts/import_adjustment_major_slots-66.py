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
        reader = csv.DictReader(csvfile, delimiter=',')
        for items in reader:
            if items['major_id'].strip() == '':
                major_full_code = items['program_id']
            else:
                major_full_code = f"{items['program_id']}0{items['major_id']}"
                
            full_major_project_code = items['project_id'] + major_full_code
            project_title = items['project_name_th']
            round_number = int(items['type'][0])
            original_slots = int(items['receive_student_number'])

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

            slot.original_slots = original_slots
            slot.current_slots = slot.original_slots
            
            slot.save()
            
            print(slot)
            
            counter += 1

    print('Imported',counter,'slots')
        

if __name__ == '__main__':
    main()
    
