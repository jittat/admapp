from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Campus, AdmissionRound, AdmissionProject, AdmissionProjectRound

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

            old_project = None
            try:
                old_project = AdmissionProject.objects.get(pk=pid)
                #old_project.delete()
            except:
                pass
            
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
                project = AdmissionProject(id=pid,
                                           title=title,
                                           short_title=short_title,
                                           short_descriptions=short_descriptions,
                                           slots=slots,
                                           max_num_selections=max_num_selections,
                                           base_fee=base_fee,
                                           cupt_code=cupt_code)
            else:
                project = old_project
                project.title = title
                project.short_title = short_title
                project.short_descriptions = short_descriptions
                project.slots = slots
                project.max_num_selections = max_num_selections
                project.base_fee = base_fee
                project.cupt_code = cupt_code
            
            if items[4] != '':
                campus = Campus.objects.get(pk=items[4])
                project.campus = campus

            project.save()

            rcount = 0
            project_round_ids = []
            round_dates = []
            for rcount in range(num_rounds):
                project_round_ids.append(int(items[7 + rcount*2]))
                round_dates.append(items[7 + rcount*2 + 1].strip())
                
            for r in range(num_rounds):
                admission_round = AdmissionRound.objects.get(pk=project_round_ids[r])

                old_project_rounds = AdmissionProjectRound.objects.filter(admission_project=project,
                                                                          admission_round=admission_round).all()
                if len(old_project_rounds) != 0:
                    project_round = old_project_rounds[0]
                else:
                    project_round = AdmissionProjectRound()
                    
                project_round.admission_project = project
                project_round.admission_round = admission_round
                project_round.admission_dates = round_dates[r]
                project_round.save()

            print('Imported:', project)
            counter += 1

    print('Imported',counter,'projects')
        

if __name__ == '__main__':
    main()
    
