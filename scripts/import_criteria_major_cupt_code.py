from django_bootstrap import bootstrap  # noqa

bootstrap()  # noqa

import sys

import xlrd
from criteria.models import MajorCuptCode
from appl.models import Faculty

from django.db.utils import IntegrityError


def main():
    filename = sys.argv[1]
    counter = 0
    with xlrd.open_workbook(filename) as workbook:
        print("start")
        worksheet = workbook.sheet_by_index(0)
        print(worksheet.nrows)
        for row in range(1, worksheet.nrows):
            try:
                faculty_name = worksheet.cell_value(row, 9)
                program_type = worksheet.cell_value(row, 20)
                program_code = worksheet.cell_value(row, 21)
                program_type_code = worksheet.cell_value(row, 19)
                major_code = worksheet.cell_value(row, 27) or ""
                title = worksheet.cell_value(row, 17)
                major_title = worksheet.cell_value(row, 28)
                print(faculty_name, program_type, program_code,
                      major_code, title, major_title)

                faculty = Faculty.objects.get(title=faculty_name)

                old_codes = MajorCuptCode.objects.filter(program_code=program_code,
                                                         major_code=major_code).all()

                if len(old_codes) != 0:
                    major_cupt_code = old_codes[0]
                    major_cupt_code.program_code=program_code
                    major_cupt_code.program_type=program_type
                    major_cupt_code.major_code=major_code
                    major_cupt_code.title=title
                    major_cupt_code.major_title=major_title
                    major_cupt_code.faculty=faculty
                    major_cupt_code.program_type_code = program_type_code
                else:
                    major_cupt_code = MajorCuptCode(program_code=program_code,
                                                    program_type=program_type,
                                                    program_type_code=program_type_code,
                                                    major_code=major_code,
                                                    title=title,
                                                    major_title=major_title,
                                                    faculty=faculty)
                major_cupt_code.save()
            except IntegrityError as e:
                s = str(e)
                print("ERROR: %s" % (s))

            counter += 1
    print('Imported', counter, 'major_cupt_code')


if __name__ == "__main__":
    main()
