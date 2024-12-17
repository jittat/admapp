from django_bootstrap import bootstrap
bootstrap()

from datetime import datetime

from regis.models import CuptConfirmation, CuptRequestQueueItem
from regis.models import LogItem, Applicant

from regis.cupt_services import cupt_check_status

import sys
import time

NEW_REQUEST_COUNT = 10

def main():
    requested = set()

    for confirmation in CuptConfirmation.objects.all():
        if confirmation.applicant_id:
            requested.add(confirmation.applicant_id)

    count = 0
    for a in Applicant.objects.all():
        if a.id not in requested:
            if CuptRequestQueueItem.objects.filter(applicant=a).count() != 0:
                continue
            CuptRequestQueueItem.create_for(a)
            count += 1
            if count == NEW_REQUEST_COUNT:
                break
            
if __name__ == '__main__':
    main()
    
