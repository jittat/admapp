from django_bootstrap import bootstrap
bootstrap()

import re
import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    result_filename = sys.argv[1]
    project_id = sys.argv[2]
    round_id = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    all_applications = {}

    for application in (ProjectApplication.objects.filter(admission_project=admission_project,
                                                          admission_round=admission_round)
                        .select_related('applicant')
                        .select_related('major_selection')
                        .all()):
        all_applications[application.applicant.national_id] = application

    counter = 0
    with open(result_filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0].strip()

            if not re.match(r'\d+',nat_id) and nat_id != '':
                continue

            if nat_id == '':
                name = ' '.join(items[1].split())
                for nat in all_applications.keys():
                    app = all_applications[nat].applicant
                    if app.first_name + ' ' + app.last_name == name:
                        nat_id = nat
            
            if nat_id not in all_applications:
                print('ERROR', nat_id, name)
                continue

            if items[1].strip() == 'ขาดสอบ':
                continue
            
            major_num = int(items[1])
            
            application = all_applications[nat_id]
            major_selection = application.major_selection
            majors = major_selection.get_majors()

            if major_num == 0:
                accepted_major = None
                for m in majors:
                    results = AdmissionResult.objects.filter(applicant=application.applicant,
                                                             application=application,
                                                             major=m,
                                                             is_accepted_for_interview=True).all()
                    if len(results)!=0:
                        accepted_major = m
                        break
                if not accepted_major:
                    print('ERROR', nat_id,'major not found',major_num)
                    continue
            else:
                accepted_major = None
                for m in majors:
                    if m.number == major_num:
                        accepted_major = m
                if not accepted_major:
                    print('ERROR', nat_id,'major not found',major_num)
                    continue

            results = AdmissionResult.objects.filter(applicant=application.applicant,
                                                    application=application,
                                                    major=accepted_major).all()
            if len(results) == 0:
                print('ERROR', nat_id,'major not found',major_num,'result not found')
                continue

            result = results[0]

            if not result.is_accepted_for_interview:
                print('ERROR', nat_id, 'did not pass for the interview')
                continue

            result.is_accepted = True
            result.updated_accepted_at = datetime.now()
            #result.clearing_house_code = items[3]
            #result.clearing_house_code_number = int(items[4])
            result.save()

            print(application.applicant, result.major)

            counter += 1

    print('Imported',counter,'results')
        

if __name__ == '__main__':
    main()
    
