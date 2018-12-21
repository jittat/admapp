from django_bootstrap import bootstrap
bootstrap()

import json
import sys

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication, Payment
from supplements.models import load_supplement_configs_with_instance

def main():
    filename = sys.argv[1]

    lines = open(filename).readlines()

    count = len(lines) // 2
    for i in range(count):
        nat_id = lines[i*2].strip()
        data = json.loads(lines[i*2+1].strip())

        if 'StatusMessage' in data:
            print('MISSING:', nat_id)
            continue

        try:
            applicant = Applicant.objects.get(national_id=nat_id)
        except:
            print('NAT-MISSING:', nat_id)
            continue
        
        if ((applicant.prefix != data['Prefix']) or
            (applicant.first_name.strip() != data['Name']) or
            (applicant.last_name.strip() != data['Surname'])):
            print('MISMATCH:',
                  nat_id,
                  applicant,
                  'vs',
                  data['Prefix'],
                  data['Name'],
                  data['Surname'])

    
if __name__ == '__main__':
    main()
    
