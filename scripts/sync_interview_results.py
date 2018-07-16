from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication
from backoffice.models import MajorInterviewCallDecision

from backoffice.views.projects import load_major_applicants
from backoffice.views.projects import load_major_applicants_no_cache
from backoffice.views.projects import load_check_marks_and_results
from backoffice.views.projects import sort_applicants_by_calculated_scores
from backoffice.views.projects import update_interview_call_status

def make_decision(project, admission_round, project_round, major, decision, fake=True):
    applicants = load_major_applicants_no_cache(project, admission_round, major)
    load_check_marks_and_results(applicants,
                                 project,
                                 admission_round,
                                 project_round)
    applicants = sort_applicants_by_calculated_scores(applicants,
                                                      project_round.criteria_check_required)
    update_interview_call_status(applicants, decision)
    call_count = len([a for a in applicants if a.is_called_for_interview])
    if call_count == decision.interview_call_count:
        print(major.number,
              major.title,
              decision.interview_call_min_score,
              decision.interview_call_count,
              'OK')
    else:
        print(major.number,
              major.title,
              decision.interview_call_min_score,
              decision.interview_call_count,
              'Mismatch %d from %d' % (call_count,decision.interview_call_count))
        #print('--------------------------')
        #for a in applicants:
        #    if a.is_called_for_interview:
        #        print(a.admission_result.calculated_score, a.admission_result.major)
        #print('--------------------------')
        
    if fake:
        return

    count = 0
    for a in applicants:
        if a.is_called_for_interview:
            res = a.admission_result
            res.is_accepted_for_interview = True
            res.updated_accepted_for_interview_at = datetime.now()
            res.save()
            count += 1
        else:
            if hasattr(a, 'admission_result'):
                res = a.admission_result
                res.is_accepted_for_interview = False
                res.updated_accepted_for_interview_at = datetime.now()
                res.save()
                count += 1
    print('Updated', count)
            

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    is_fake = len(sys.argv) < 4 or (sys.argv[3] != 'real')
    
    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)
    project_round = admission_project.get_project_round_for(admission_round)

    majors = admission_project.major_set.order_by('number').all()
    interview_decisions = dict([(m.number, MajorInterviewCallDecision.get_for(m, admission_round))
                                for m in majors])

    for number, major in sorted([(m.number,m) for m in majors]):
        decision = interview_decisions[number]
        if decision:
            make_decision(admission_project,
                          admission_round,
                          project_round,
                          major,
                          decision,
                          is_fake)
        else:
            print(number, major.title, 'NO-CALL')
    
    
if __name__ == '__main__':
    main()
