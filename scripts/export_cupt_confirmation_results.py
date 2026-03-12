from django_bootstrap import bootstrap
bootstrap()

from datetime import datetime

from regis.models import Applicant, CuptConfirmation, CuptRequestQueueItem
from regis.models import LogItem

import sys

def main():
    nat_id_filename = sys.argv[1]
    for line in open(nat_id_filename):
        nat_id = line.strip()
        try:
            applicant = Applicant.objects.get(national_id=nat_id)
        except Applicant.DoesNotExist:
            applicant = None
        
        if applicant == None:
            continue

        if hasattr(applicant,'cupt_confirmation'):
            cupt_confirmation = applicant.cupt_confirmation
        else:
            cupt_confirmation = None

        if cupt_confirmation != None:
            print(",".join([applicant.national_id, 
                            applicant.first_name, 
                            applicant.last_name, 
                            str(cupt_confirmation.has_confirmed),
                            str(cupt_confirmation.has_registered),
                            str(cupt_confirmation.api_result_code)]))
            
if __name__ == '__main__':
    main()
    
