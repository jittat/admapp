from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import Faculty
from backoffice.models import AdjustmentMajor
from criteria.models import MajorCuptCode

def main():
    counter = 0
    for cupt_code in MajorCuptCode.objects.all():
        faculty = cupt_code.faculty
        full_code = cupt_code.get_program_major_code_as_str()

        old_adj_majors = AdjustmentMajor.objects.filter(full_code=full_code).all()
        if len(old_adj_majors)!=0:
            adj_major = old_adj_majors[0]
        else:
            adj_major = AdjustmentMajor()

        adj_major.full_code = full_code
        adj_major.title = str(cupt_code)
        adj_major.faculty = faculty
        adj_major.major_code = full_code
        adj_major.study_type_code = cupt_code.program_type_code
        adj_major.save()

        print(adj_major, faculty, adj_major.major_code, adj_major.study_type_code)
            
        counter += 1

    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
