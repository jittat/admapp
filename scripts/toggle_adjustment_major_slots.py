from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from backoffice.models import AdjustmentMajorSlot

def main():
    round_number = sys.argv[1]
    command = sys.argv[2]

    COMMANDS = {
        'finalize': ('is_final', True),
        'unfinalize': ('is_final', False),
        'freeze': ('is_frozen', True),
        'unfreeze': ('is_frozen', False),
        'confirm': ('is_confirmed_by_faculty', True),
        'unconfirm': ('is_confirmed_by_faculty', False),
    }

    if command not in COMMANDS.keys():
        print('ERROR command not found.  Should be in', COMMANDS.keys())
        quit()
        
    counter = 0

    for slot in AdjustmentMajorSlot.objects.filter(admission_round_id=round_number):
        f = COMMANDS[command][0]
        v = COMMANDS[command][1]
        setattr(slot,f,v)
        slot.save()
        counter += 1

    print('Updated', counter, 'slots')

if __name__ == '__main__':
    main()
    
