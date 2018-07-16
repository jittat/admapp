from django_bootstrap import bootstrap
bootstrap()

from datetime import datetime

from regis.models import Applicant
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

    natfilename = sys.argv[2]
    
    client = create_cupt_client()

    if not token:
        token = get_token(client)
        if token_filename != '':
            save_token(token_filename, token)

    lines = open(natfilename).readlines()
    for l in lines:
        national_id = l.strip()
        if national_id == "":
            continue
        
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

        if has_confirmed:
            print(national_id,1)
        else:
            print(national_id,0)
            
if __name__ == '__main__':
    main()
    
