from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from django.contrib.auth.models import User
from appl.models import Faculty, AdmissionRound
from backoffice.models import AdjustmentMajor, AdjustmentMajorSlot

def combine_titles(slots):
    extras = []
    main = ''
    for s in slots:
        ex = ' '.join(s.admission_project_title.split(' ')[2:])
        main = ' '.join(s.admission_project_title.split(' ')[:2])

        if ex.startswith('(') and ex.endswith(')'):
            ex = ex[1:-1]
        
        extras.append(ex)

    new_title = main + ' ' + '/'.join(extras)

    if len(new_title) > 150:
        new_title = new_title[:150] + '...'
    return new_title
        
def main():
    filename = sys.argv[1]
    counter = 0

    join_set = {}
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            if row['join_id'] == '0':
                continue

            join_id = row['join_id']
            if join_id not in join_set:
                join_set[join_id] = []

            join_set[join_id].append(row['key'])

    for join_id in join_set:
        slots = [
            AdjustmentMajorSlot.objects.get(cupt_code=cupt_code)
            for cupt_code in join_set[join_id]
        ]

        current_slots = slots[0].current_slots
        for s in slots:
            if s.current_slots != current_slots:
                print('ERROR', slots)

        new_title = combine_titles(slots)
        slot = slots[0]

        slot.admission_project_title = new_title
        slot.save()

        for s in slots[1:]:
            s.delete()
        #print(join_id, new_title)

if __name__ == '__main__':
    main()
    
