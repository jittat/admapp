from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound
from backoffice.models import MajorInterviewCallDecision

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    majors = admission_project.major_set.all()

    for m in majors:
        call_decision = MajorInterviewCallDecision.get_for(m, admission_round)
        if not call_decision:
            call_decision = MajorInterviewCallDecision(admission_round=admission_round,
                                                       major=m,
                                                       admission_project=admission_project)

        call_decision.interview_call_min_score = 0

        from datetime import datetime
        call_decision.updated_at = datetime.now()
        call_decision.save()

if __name__ == '__main__':
    main()
    
