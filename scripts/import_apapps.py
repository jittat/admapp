from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from supplements.models import AdvancedPlacementApplicant, AdvancedPlacementResult

def main():
    app_filename = sys.argv[1]
    result_filename = sys.argv[2]
    
    counter = 0
    with open(app_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for items in reader:
            if len(items) < 2:
                continue

            nat_id = items[0]

            old_app = None
            try:
                old_app = AdvancedPlacementApplicant.objects.get(national_id=nat_id)
            except:
                pass

            if old_app:
                continue
            
            app = AdvancedPlacementApplicant(national_id=nat_id,
                                             student_id=items[0])
            app.save()
            counter += 1

    print('Imported',counter,'applicants')
        
    for r in AdvancedPlacementResult.objects.all():
        r.delete()

    counter = 0
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for items in reader:
            if len(items) < 4:
                continue

            std_id = items[0]

            app = AdvancedPlacementApplicant.objects.get(student_id=std_id)

            res = AdvancedPlacementResult(ap_applicant=app,
                                          subject_id=items[5],
                                          section_id=1,
                                          grade=items[12])
            res.save()
            
            counter += 1

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
