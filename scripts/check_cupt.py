from django_bootstrap import bootstrap
bootstrap()

from datetime import datetime

from regis.models import CuptConfirmation, CuptRequestQueueItem
from regis.models import LogItem

from regis.cupt_services import create_cupt_client, get_token, check_permission

import sys

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
    if len(sys.argv) >= 2:
        token_filename = sys.argv[1]

    if token_filename != '':
        token = read_token(token_filename)
    else:
        token = None
        
    queue_item = CuptRequestQueueItem.objects.first()

    if not queue_item:
        return
    
    client = create_cupt_client()

    if not token:
        token = get_token(client)
        if token_filename != '':
            save_token(token_filename, token)
            
    while queue_item:
        applicant = queue_item.applicant

        national_id = applicant.national_id
        if applicant.has_registered_with_passport():
            national_id = applicant.passport_number
            
        ok, result = check_permission(client, token, national_id)
        print(ok, result)

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

        LogItem.create('CUPT QUERY result = ' + result, applicant)

        if ok:
            if hasattr(applicant,'cupt_confirmation'):
                cupt_confirmation = applicant.cupt_confirmation
            else:
                cupt_confirmation = CuptConfirmation(applicant=applicant)

            cupt_confirmation.national_id = applicant.national_id
            cupt_confirmation.passport_number = applicant.passport_number
            cupt_confirmation.updated_at = datetime.now()
            cupt_confirmation.has_confirmed = has_confirmed
            cupt_confirmation.save()

        queue_item.delete()
        queue_item = CuptRequestQueueItem.objects.first()
            
if __name__ == '__main__':
    main()
    
