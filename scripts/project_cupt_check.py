from django_bootstrap import bootstrap
bootstrap()

from datetime import datetime

from regis.models import Applicant
from regis.models import CuptConfirmation, CuptRequestQueueItem
from regis.models import LogItem
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication, Payment

from regis.cupt_services import create_cupt_client, get_token, check_permission

import sys
import time

def read_token(filename):
    try:
        lines = open(filename).readlines()
        return lines[0].strip()
    except:
        return None

def save_token(filename, token):
    f = open(filename,'w')
    f.write(token)
    f.close()

def main():
    token_filename = ''
    if len(sys.argv) >= 4:
        token_filename = sys.argv[3]

    if token_filename != '':
        token = read_token(token_filename)
    else:
        token = None

    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    applications = ProjectApplication.objects.filter(admission_project=admission_project,
                                                     admission_round=admission_round,
                                                     is_canceled=False).all()

    client = create_cupt_client()

    if not token:
        token = get_token(client)
        if token_filename != '':
            save_token(token_filename, token)
            
    for application in applications:
        applicant = application.applicant
        national_id = applicant.national_id
        if applicant.has_registered_with_passport():
            national_id = applicant.passport_number
            
        ok, result = check_permission(client, token, national_id)

        has_confirmed = True
        
        if not ok:
            if result == 'token-expired':
                token = get_token(client)
                if token_filename != '':
                    save_token(token_filename, token)
                    
                ok, result = check_permission(client, token, national_id)
            elif result == 'id-not-valid':
                ok = True
                has_confirmed = False

        if ok:
            if result == '0' or result == 'X':
                has_confirmed = False

        if ok:
            print(national_id, has_confirmed)

        time.sleep(0.1)
            
if __name__ == '__main__':
    main()
    
