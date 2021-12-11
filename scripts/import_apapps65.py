from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from supplements.models import AdvancedPlacementApplicant, AdvancedPlacementResult

def main():
    appresult_filename = sys.argv[1]

    counter = 0
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
            
            nat_id = items[0]

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

            for result in AdvancedPlacementResult.objects.filter(ap_applicant=app).all():
                result.delete()

            for sid in range(subject_count):
                subject_id = header[4 + sid]

                if items[4 + sid].strip() != '_':
                    res = AdvancedPlacementResult(ap_applicant=app,
                                                  subject_id=subject_id,
                                                  section_id='1',
                                                  grade=items[4 + sid].strip())
                    res.save()

            print(items)
            counter += 1

    print('Imported',counter,'applicants')

if __name__ == '__main__':
    main()
    
