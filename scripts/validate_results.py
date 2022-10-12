from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound


def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    filename = sys.argv[3]

    csvfile = open(filename)
    reader = csv.reader(csvfile)
    next(reader)
    next(reader)

    accepted_count = 0
    for items in reader:
        major_code = items[0]
        application_number = items[4]
        national_id = items[5]

        applicant = Applicant.find_by_national_id(national_id)
        if not applicant:
            applicant = Applicant.find_by_passport_number(national_id)

        if not applicant:
            print('ERROR applicant not found', national_id)

        results = AdmissionResult.objects.filter(applicant=applicant,
                                                 admission_project=project,
                                                 admission_round=admission_round).all()

        found = False
        for r in results:
            result_major = r.major
            result_major_code = result_major.get_full_major_cupt_code(project)
            if result_major_code == major_code:
                found = True
                if not r.is_accepted:
                    print('ERROR should not accepted:', applicant, major_code, result_major)
            else:
                if r.is_accepted:
                    print('ERROR should accepted:', applicant, major_code, result_major)
        if not found:
            print('ERROR not found:', applicant, major_code)
            
        #print(applicant, len(results))
        accepted_count += 1

    all_accepted_results = [r for r in AdmissionResult.objects.filter(admission_project=project,
                                                                      admission_round=admission_round).all()
                            if r.is_accepted]

    if accepted_count != len(all_accepted_results):
        print('ERROR not all accepted - in file =', accepted_count,'in system =', len(all_accepted_results))
    
    
if __name__ == '__main__':
    main()
    
