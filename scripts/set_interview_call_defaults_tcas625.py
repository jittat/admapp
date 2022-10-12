from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound
from backoffice.models import MajorInterviewCallDecision

def main():
    result_filename = sys.argv[1]
    project_id = sys.argv[2]
    round_id = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    scores = {}
    
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            major_number = int(items[0])
            nat_id = items[1]
            score = float(items[2])

            applicant = Applicant.objects.get(national_id=nat_id)
            results = AdmissionResult.objects.filter(applicant=applicant,
                                                    admission_project=admission_project,
                                                    admission_round=admission_round).all()
            if len(results) != 1:
                print('ERROR', nat_id, major_number)

            result = results[0]
            if result.major.number != major_number:
                print('ERROR major number', nat_id, major_number)

            if result.is_criteria_passed == False:
                print('skipping: ', nat_id)
                continue
            
            if major_number not in scores:
                scores[major_number] = []

            scores[major_number].append(-score)

    for k in scores.keys():
        scores[k] = sorted(scores[k])

    majors = admission_project.major_set.all()

    for m in majors:
        slots = m.slots
        number = m.number
        if number not in scores:
            scores[number] = []
        if slots == 0:
            continue
        
        if len(scores[number]) <= slots:
            min_score = 0
        else:
            min_score = -scores[number][slots-1]
            if min_score < 0:
                min_score = 0

        call_decision = MajorInterviewCallDecision.get_for(m, admission_round)
        if not call_decision:
            call_decision = MajorInterviewCallDecision(admission_round=admission_round,
                                                       major=m,
                                                       admission_project=admission_project)

        call_decision.interview_call_min_score = min_score
        call_decision.interview_call_count = len([s for s in scores[number]
                                                  if s < - min_score + MajorInterviewCallDecision.FLOAT_DELTA])
        from datetime import datetime
        call_decision.updated_at = datetime.now()
        call_decision.save()
        print(number, call_decision.interview_call_min_score, slots, call_decision.interview_call_count)

if __name__ == '__main__':
    main()
    
