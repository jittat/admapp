from django_bootstrap import bootstrap
bootstrap()

from random import choice

from regis.models import Applicant
from appl.models import PersonalProfile

ALPHAS = 'abcdefghijklmnopqrstuvwxyz'
DIGITS = '0123456789'

def random_id():
    return ''.join([choice(DIGITS) for _ in range(13)])

def random_name():
    return ''.join([choice(ALPHAS) for _ in range(15)])

def random_short():
    return ''.join([choice(ALPHAS) for _ in range(5)])

def apply_random(o, fields):
    for t,func,fs in fields:
        for f in fs:
            if getattr(o,f) != '':
                setattr(o, f, func())

def main():
    APP_FILEDS = [
        ('ids', random_id, ['national_id','passport_number']),
        ('names', random_name, ['first_name', 'last_name']),
    ]
    PERSONAL_FIELDS = [
        ('names', random_name, ['father_first_name', 'father_last_name',
                                'mother_first_name', 'mother_last_name',
                                'first_name_english', 'last_name_english']),
        ('phone', random_id, ['contact_phone', 'mobile_phone']),
        ('addr', random_short, ['house_number', 'avenue',
                                'road', 'sub_district', 'district',
                                'province', 'postal_code']),
    ]

    counter = 0
    for a in Applicant.objects.all():
        counter += 1
        if counter % 1000 == 0:
            print(counter, a)

        apply_random(a, APP_FILEDS)
        a.save()
        
        personal_profile = a.get_personal_profile()
        if personal_profile:
            apply_random(personal_profile, PERSONAL_FIELDS)
            personal_profile.save()

        if counter % 1000 == 0:
            print(a)

if __name__ == '__main__':
    main()
    
