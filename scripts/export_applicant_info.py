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

        address = profile.get_full_address().replace('"','""')
        
        print(','.join([applicant.national_id,
                        applicant.prefix,
                        applicant.first_name,
                        applicant.last_name,
                        profile.prefix_english,
                        profile.first_name_english,
                        profile.last_name_english,
                        applicant.email,
                        profile.contact_phone,
                        profile.mobile_phone,
                        '"' + address + '"', ]))

    
if __name__ == '__main__':
    main()
    
