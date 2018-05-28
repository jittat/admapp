from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant
        
def main():
    lines = []
    while True:
        try:
            l = input()
            lines.append(l.strip())
        except:
            break

    for l in lines:
        applicant = Applicant.objects.get(national_id=l)
        profile = applicant.get_personal_profile()
        print(','.join([applicant.national_id,applicant.get_full_name(), applicant.email, profile.contact_phone, profile.mobile_phone]))

    
if __name__ == '__main__':
    main()
    
