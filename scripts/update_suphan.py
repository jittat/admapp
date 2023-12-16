from django_bootstrap import bootstrap
bootstrap()

from appl.models import Campus, Major
from criteria.models import MajorCuptCode

PROGRAM_CODE_UPDATES = {
    '10020118620102A': ('10020535620102A',['B','C']),
    '10020118620101A': ('10020535620101A',['']),
}

def main():
    campus = Campus.objects.get(pk=5)
    campus.title = 'สำนักงานเขตบริหารการเรียนรู้พื้นที่สุพรรณบุรี'
    campus.save()
    
    for p in PROGRAM_CODE_UPDATES:
        codes = MajorCuptCode.objects.filter(program_code=p).all()
        for c in codes:
            c.program_code = PROGRAM_CODE_UPDATES[p][0]
            print(c)
            c.save()

    for p in PROGRAM_CODE_UPDATES:
        mcodelist = PROGRAM_CODE_UPDATES[p][1]
        for mcode in mcodelist:
            full_code = p
            new_code = PROGRAM_CODE_UPDATES[p][0]
            if mcode != '':
                full_code += '0'+mcode
                new_code += '0'+mcode
            majors = Major.objects.filter(cupt_full_code=full_code)
            if len(majors) > 0:
                m = majors[0]
                print(full_code, new_code, m)
                m.cupt_full_code = new_code
                m.save()

if __name__ == '__main__':
    main()
    
