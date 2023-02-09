from django_bootstrap import bootstrap  # noqa

bootstrap()  # noqa

import sys

from random import choice
from criteria.models import MajorCuptCode
from appl.models import Faculty

HEADER = [
    'username',
    'firstname',
    'lastname',
    'password',
    'full_code',
    'faculty_title',
]

ALPHA = '23456789abcdefghijklmnpqrstuvwzyz'

def random_password():
    return ''.join([choice(ALPHA) for _ in range(6)])

def get_major_user_name(faculty, num, cupt_code):
    return f'z{faculty.id:02d}{num:03d}'

def get_faculty_user_name(faculty, num, cupt_code):
    return f'y{faculty.id:02d}'

def export_num_adjustment_users(user_name_function,
                                user_title_function,
                                only_first_major):
    codes = [c for _,_,c in sorted([(c.faculty_id, c.get_program_major_code(), c) for c in MajorCuptCode.objects.all()])]

    print(','.join(HEADER))
    
    num = 0
    prev_faculty = -1
    for c in codes:
        if c.faculty_id != prev_faculty:
            num = 1
        else:
            num += 1
        prev_faculty = c.faculty_id
        items = [user_name_function(c.faculty, num, c),
                 user_title_function(c),
                 'ปรับจำนวน',
                 random_password(),
                 c.get_program_major_code_as_str(),
                 str(c.faculty)]
        if only_first_major:
            items[4] = 0
        if (not only_first_major) or (num == 1):
            print(','.join([str(x) for x in items]))

def export_num_adjustment_major_users():
    export_num_adjustment_users(get_major_user_name,
                                lambda c: str(c),
                                False)
    
def export_num_adjustment_faculty_users():
    export_num_adjustment_users(get_faculty_user_name,
                                lambda c: str(c.faculty),
                                True)
    
def main():
    if '--faculty' in sys.argv:
        export_num_adjustment_faculty_users()
    else:
        export_num_adjustment_major_users()


if __name__ == '__main__':
    main()
