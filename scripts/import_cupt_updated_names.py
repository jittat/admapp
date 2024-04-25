from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import json

from regis.models import Applicant, CuptUpdatedName

def main():
    update_json = sys.argv[1]

    updates = json.loads(open(update_json).read())

    for national_id in updates:
        applicant = Applicant.find_by_national_id(national_id)
        if not applicant:
            applicant = Applicant.find_by_passport_number(national_id)

        if not applicant:
            print('ERROR applicant not found', national_id)
            continue

        current_updates = {
            u.field_name: u
            for u in CuptUpdatedName.objects.filter(applicant=applicant).all()
        }

        for f in updates[national_id]:
            if f in current_updates:
                up = current_updates[f]
            else:
                up = CuptUpdatedName(applicant=applicant,
                                     field_name=f)

            up.updated_value = updates[national_id][f]
            up.save()
            print(applicant, up.field_name, up.updated_value)
        
if __name__ == '__main__':
    main()
    
