from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from supplements.models import AdvancedPlacementApplicant, AdvancedPlacementResult

def main():
    appresult_filename = sys.argv[1]

    counter = 0

    first_row_for_app = True
    old_nat_id = ''

    SUBJECT_COL = 9
    GRADE_COL = 16
    
    with open(appresult_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        first_line = True
        
        for items in reader:
            if len(items) < 2:
                continue

            if first_line:
                header = items
                subject_count =  len(header) - 4
                first_line = False
                continue
            
            nat_id = items[0].strip()
            
            if nat_id == '':
                continue
            
            first_row_for_app = old_nat_id != nat_id
            old_nat_id = nat_id
                
            app = None
            try:
                app = AdvancedPlacementApplicant.objects.get(national_id=nat_id)
            except:
                pass

            if not app:
                app = AdvancedPlacementApplicant(national_id=nat_id,
                                                 student_id=nat_id)
            else:
                app.student_id = nat_id
                
            app.save()

            if first_row_for_app:
                for result in AdvancedPlacementResult.objects.filter(ap_applicant=app).all():
                    result.delete()

            subject_id = items[SUBJECT_COL].strip()
            grade = items[GRADE_COL].strip()

            if (grade != '') and (grade != 'N'):
                res = AdvancedPlacementResult(ap_applicant=app,
                                              subject_id=subject_id,
                                              section_id='1',
                                              grade=grade)
                res.save()

            #print(items)
            if first_row_for_app:
                counter += 1

            if counter % 100 == 0:
                print(items)

    print('Imported',counter,'applicants')

if __name__ == '__main__':
    main()
    
