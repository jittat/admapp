from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from regis.models import Applicant
from appl.models import ExamScore

def main():
    score_filename = sys.argv[1]
    exam_type = sys.argv[2]

    counter = 0
    with open(score_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        first_line = True
        for items in reader:
            if first_line:
                exams = items[5:]
                exam_list = ','.join(exams)
                first_line = False
                continue

            if len(items) < 4:
                continue
            
            nat_id = items[0]

            try:
                applicant = Applicant.objects.get(national_id=nat_id)
            except Applicant.DoesNotExist:
                print('ERROR not found', nat_id)
                continue

            old_scores = applicant.examscore_set.filter(exam_type=exam_type,
                                                        exam_round=items[4]).all()
            for o in old_scores:
                o.delete()

            sc = ExamScore(applicant=applicant,
                           exam_type=exam_type)
            sc.exam_round = items[4]
            sc.exam_list = exam_list
            sc.score_list = ','.join(items[5:])
            sc.save()

            counter += 1
            if counter % 100 == 0:
                print(counter)

    print('Imported',counter,'applicants')
        
if __name__ == '__main__':
    main()
    
