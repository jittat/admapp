from django_bootstrap import bootstrap
bootstrap()

from datetime import datetime

from regis.models import CuptConfirmation, CuptRequestQueueItem
from regis.models import LogItem

from regis.cupt_services import cupt_check_status

import sys
import time

INTERVAL_WAIT = 0.2

def main():
    queue_item = CuptRequestQueueItem.objects.first()

    if not queue_item:
        return
    
    while queue_item:
        applicant = queue_item.applicant

        national_id = applicant.national_id
        if applicant.has_registered_with_passport():
            national_id = applicant.passport_number.upper()
        first_name = applicant.first_name
        last_name = applicant.last_name
            
        result, messages = cupt_check_status(national_id, first_name, last_name)
        print(national_id, result)

        REGISTERED_CODES = [1,2,3]
        has_registered = False
        has_confirmed = False
        
        if 'code' in result:
            if result['code'] in REGISTERED_CODES:
                has_registered = True
        
        LogItem.create('CUPT QUERY result = ' + messages, applicant)

        if 'code' in result:
            if hasattr(applicant,'cupt_confirmation'):
                cupt_confirmation = applicant.cupt_confirmation
            else:
                cupt_confirmation = CuptConfirmation(applicant=applicant)

            cupt_confirmation.national_id = applicant.national_id
            cupt_confirmation.passport_number = applicant.passport_number
            cupt_confirmation.updated_at = datetime.now()
            cupt_confirmation.has_confirmed = has_confirmed
            cupt_confirmation.has_registered = has_registered
            cupt_confirmation.api_result_code = result['code']
            cupt_confirmation.save()            

        queue_item.delete()
        queue_item = CuptRequestQueueItem.objects.first()

        time.sleep(INTERVAL_WAIT)
            
if __name__ == '__main__':
    main()
    
