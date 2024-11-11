from django_bootstrap import bootstrap  # noqa

bootstrap()  # noqa

import sys

from random import choice
from criteria.models import MajorCuptCode
from appl.models import Faculty, AdmissionProject, Major

HEADER = [
    'username',
    'firstname',
    'lastname',
    'password',
    'proj',
    'fac',
    'major',
]

ALPHA = '23456789abcdefghijklmnpqrstuvwzyz'

def random_password():
    return ''.join([choice(ALPHA) for _ in range(6)])

def get_major_user_name(project_codename, faculty, num, major):
    return f'{project_codename}{num:d}m'

def get_faculty_user_name(project_codename, faculty, num, major):
    return f'{project_codename}{faculty.id:d}f'

def build_uniform_major_num(majors):
    major_nums = {}
    c = 0
    for fid,title in sorted(list(set([(m.faculty_id, m.title) for m in majors]))):
        c += 1
        major_nums[(fid,title)] = c

    return major_nums

def export_num_adjustment_users(projects,
                                codenames,
                                user_name_function,
                                user_title_function,
                                only_first_major):
    majors = []
    for p in projects:
        majors += list(p.major_set.all())
    major_nums = build_uniform_major_num(majors)
    
    print(','.join(HEADER))
    
    num = 0
    prev_faculty = -1
    first = True
    for m in majors:
        project = m.admission_project
        project_codename = codenames[project.id]

        num = major_nums[(m.faculty_id,m.title)]
        
        items = [user_name_function(project_codename, m.faculty, num, m),
                 user_title_function(m),
                 project,
                 random_password(),
                 project.id,
                 m.faculty_id,
                 m.number]
        if only_first_major:
            items[6] = 0

        if prev_faculty != (project.id, m.faculty_id):
            first = True
        else:
            first = False
        prev_faculty = (project.id, m.faculty_id)

        if (not only_first_major) or (first):
            print(','.join([str(x) for x in items]))

def export_num_adjustment_major_users(projects, codenames):
    export_num_adjustment_users(projects,
                                codenames,
                                get_major_user_name,
                                lambda c: str(c),
                                False)
    
def export_num_adjustment_faculty_users(projects, codenames):
    export_num_adjustment_users(projects,
                                codenames,
                                get_faculty_user_name,
                                lambda c: str(c.faculty),
                                True)

PROJECT_CODENAMES = {
    1: {
        1: 'elea',
        2: 'ap',
        3: 'intera',
        4: 'nspr',
        8: 'dpst',
        9: 'posna',
        32: 'steam',
    },
    101: {
        101: 'eleb',
        103: 'interb',
        109: 'posnb',
        33: 'smt',
    },
    2: {
        11: 'kus',
        12: 'seed',
        13: 'diam',
        14: 'pir',
        16: 'prov',
        17: 'sprt',
        18: 'cul',
        23: 'mou',
        24: 'vet',
        34: 'spe',
	35: 'med',
        50: 'int2',
    },
    3: {
        28: 'kuad',
    },
    4: {
        31: 'ind',
    },
}
    
def main():
    round_id = [int(x) for x in sys.argv[1:] if not x.startswith('-')][0]

    projects = [AdmissionProject.objects.get(pk=id)
                for id in PROJECT_CODENAMES[round_id].keys()]
    if '--faculty' in sys.argv:
        export_num_adjustment_faculty_users(projects,
                                            PROJECT_CODENAMES[round_id])
    else:
        export_num_adjustment_major_users(projects,
                                          PROJECT_CODENAMES[round_id])


if __name__ == '__main__':
    main()
