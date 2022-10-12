from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Campus, AdmissionRound, AdmissionProject


def main():
    admission_rounds = dict([(r.id,r) for r in AdmissionRound.objects.all()])
    
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            if len(items) < 7:
                continue
            if items[0] == 'id':
                continue

            pid = int(items[0])

            try:
                old_project = AdmissionProject.objects.get(pk=pid)
            except:
                old_project = None
            
            title = items[1]
            short_title = items[2]
            short_descriptions = items[3]
            slots = int(items[5])
            num_rounds = int(items[6])

            next_col_base = 7 + num_rounds*2
            max_num_selections = int(items[next_col_base])
            base_fee = int(items[next_col_base + 1])
            cupt_code = items[next_col_base + 2]

            if not old_project:
                print('ERROR old project not found')
                continue

            project = old_project
            
            project.title=title
            project.short_title=short_title
            project.short_descriptions=short_descriptions
            project.slots=slots
            project.max_num_selections=max_num_selections
            project.base_fee=base_fee
            project.cupt_code=cupt_code
            
            if items[4] != '':
                campus = Campus.objects.get(pk=items[4])
                project.campus = campus

            project.save()

            print('Updated:', project)
            counter += 1

    print('Updated',counter,'projects')
        

if __name__ == '__main__':
    main()
    
