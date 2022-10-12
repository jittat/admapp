from django_bootstrap import bootstrap
bootstrap()

from appl.models import Major
from criteria.models import  MajorCuptCode

MAJOR_UPDATES = {
    '10020107611102A': {
        'new_program_code': '10020107611106A',
        'new_title': 'ศบ. สาขาวิชาเศรษฐศาสตร์ประยุกต์และธุรกิจเกษตร',
    },
    '10020107611102B': {
        'new_program_code': '10020107611106B',
        'new_title': 'ศบ. สาขาวิชาเศรษฐศาสตร์ประยุกต์และธุรกิจเกษตร',
    },
    '10020326610501A': {
        'new_program_code': '10020326610502A',
        'new_title': 'บธ.บ. สาขาวิชาการบัญชี',
    },
    '10020326610501B': {
        'new_program_code': '10020326610502B',
        'new_title': 'บธ.บ. สาขาวิชาการบัญชี',
    },
}

def main():
    for program_code in MAJOR_UPDATES:
        codes = MajorCuptCode.objects.filter(program_code=program_code)

        print(f'{program_code}:')
        
        update = MAJOR_UPDATES[program_code]
        for c in codes:
            c.program_code = update['new_program_code']
            c.title = update['new_title']
            c.save()
            print(c)

        majors = Major.objects.filter(detail_items_csv__contains=program_code)
        for m in majors:
            m.detail_items_csv = m.detail_items_csv.replace(program_code,
                                                            update['new_program_code'])
            m.title = update['new_title']
            m.save()
            print(m)

if __name__ == '__main__':
    main()
