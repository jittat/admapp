from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant

def build_address(profile):
    address_items = []
    address_items.append(profile.house_number)

    ADDR_ITEMS = [
        ('หมู่ ','village_number'),
        ('ซ.','avenue'),
        ('ถ.','road'),
        ('','sub_district'),
        ('','district'),
        ('','province'),
        ('','postal_code'),
    ]
    
    for pref, f in ADDR_ITEMS:
        val = getattr(profile,f)
        if val.strip() != '' and val.strip() != '-':
            address_items.append(pref + val)
           
    return ' '.join(address_items)
            
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

        address = build_address(profile).replace('"','""')
        
        print(','.join([applicant.national_id,
                        applicant.get_full_name(),
                        applicant.email,
                        profile.contact_phone,
                        profile.mobile_phone,
                        '"' + address + '"', ]))

    
if __name__ == '__main__':
    main()
    
