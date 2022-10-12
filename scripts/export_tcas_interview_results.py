from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionResult, AdmissionRound


def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    results = AdmissionResult.objects.filter(admission_project=admission_project,
                                             admission_round=admission_round).all()

    for res in results:
        if res.is_accepted_for_interview: # and res.is_tcas_confirmed:
            if res.is_interview_absent:
                r = '2'
            elif res.is_accepted:
                r = '1'
            elif res.is_accepted == False:
                r = '4'
            else:
                r = 'XXXXX'
            items = [res.applicant.national_id,
                     res.applicant.national_id[1:],
                     res.applicant.get_full_name(),
                     str(res.major.number),
                     res.major.title,
                     r]
            print(','.join(items))

if __name__ == '__main__':
    main()
    
