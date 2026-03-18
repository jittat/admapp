from django_bootstrap import bootstrap
bootstrap()

import sys

from backoffice.models import AdjustmentMajorSlot
from appl.models import AdmissionRound

def print_slot(slot):
    r = slot.admission_round_number
    faculty = slot.faculty
    data = [
        slot.project_code()[1:],
        slot.project_code(),
        faculty.campus.title + ' ' + faculty.title,
        slot.major_full_code,
        slot.cupt_code,
        slot.adjustment_major.title,
        slot.original_slots,
        slot.current_slots,
    ]

    print(','.join([str(item) for item in data]))


def main():
    round_id = sys.argv[1]
    admission_round = AdmissionRound.objects.get(pk=round_id)
    adjustment_slots = AdjustmentMajorSlot.objects.filter(admission_round=admission_round).all()

    for slot in adjustment_slots:
        if slot.current_slots != slot.original_slots:
            print_slot(slot)

    
if __name__ == '__main__':
    main()
    
