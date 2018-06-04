from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication
from backoffice.models import MajorInterviewCallDecision

from backoffice.views.projects import load_major_applicants
from backoffice.views.projects import load_check_marks_and_results
from backoffice.views.projects import sort_applicants_by_calculated_scores
from backoffice.views.projects import update_interview_call_status

def make_calls(project, admission_round, project_round, major, confirmed_applicants, fake=True):
    all_applicants = load_major_applicants(project, admission_round, major, load_results=True)
    applicants = sort_applicants_by_calculated_scores(all_applicants,
                                                      project_round.criteria_check_required)

    candidates = []
    free_candidates = []
    
    slots = major.slots
    confirmed_count = 0
    for a in applicants:
        if hasattr(a,'admission_result'):
            result = a.admission_result
            if result.is_accepted_for_interview and result.tcas_acceptance_round_number == 1:
                if result.is_tcas_confirmed:
                    confirmed_count += 1
            else:
                if result.calculated_score >= 0:
                    candidates.append(a)
                    if a.national_id not in confirmed_applicants:
                        free_candidates.append(a)

    call_count = slots - confirmed_count
    if call_count <= 0:
        print(major.number,
              major.title,
              slots,
              confirmed_count,
              'FULL')
        return

    if call_count > len(free_candidates):
        min_score = 0
    else:
        min_score = free_candidates[call_count-1].admission_result.calculated_score

    accepted_count = len([a for a in free_candidates
                          if a.admission_result.calculated_score > min_score - MajorInterviewCallDecision.FLOAT_DELTA])

    if accepted_count > 0:
        print(major.number,
              major.title,
              slots,
              confirmed_count,
              accepted_count)
    else:
        print(major.number,
              major.title,
              slots,
              confirmed_count,
              'EMPTY')
        
    if fake:
        return

    count = 0
    for a in candidates:
        if a.admission_result.calculated_score > min_score - MajorInterviewCallDecision.FLOAT_DELTA:
            result = a.admission_result

            if a.national_id not in confirmed_applicants:
                result.is_accepted_for_interview = True
                result.tcas_acceptance_round_number = 2
            else:
                result.is_tcas_canceled = True
                
            result.save()
            count += 1

    
    print('Updated', count)
            

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    confirmation_filename = sys.argv[3]
    natid_map_filename = sys.argv[4]

    is_fake = len(sys.argv) < 6 or (sys.argv[5] != 'real')
    
    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)
    project_round = admission_project.get_project_round_for(admission_round)

    majors = admission_project.major_set.order_by('number').all()

    natid_map = dict([(f[0],f[1]) for f in
                      [l.strip().split(',') for l in
                       open(natid_map_filename).readlines()]])
    confirmed_applicants = set([natid_map[n] for n in
                                [l.strip().split(',')[0] for l in
                                 open(confirmation_filename, encoding='tis-620').readlines()][1:]])
    
    for number, major in sorted([(m.number,m) for m in majors]):
        make_calls(admission_project,
                   admission_round,
                   project_round,
                   major,
                   confirmed_applicants,
                   is_fake)

        
if __name__ == '__main__':
    main()
