from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    filename = sys.argv[1]

    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for items in reader:
            nat_id = items[0]
            applicant = Applicant.objects.get(national_id=nat_id)
            CuptRequestQueueItem.create_for(applicant)
            print(applicant)
            counter += 1

        print(counter,'queued')


if __name__ == '__main__':
    main()
    
