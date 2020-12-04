from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from appl.models import AdmissionProject, AdmissionRound, Faculty
from criteria.models import AdmissionCriteria, COMPONENT_WEIGHT_TYPE_CHOICES

def render_score_criterias(score_criterias, hide_percent=False, short=False):
    lines = []
    counter = 0
    for s in score_criterias:
        if not hide_percent:
            if not short:
                sdisplay = str(s)
            else:
                sdisplay = s.display_with_short_relation()
        else:
            sdisplay = s.description

        counter += 1
        lines.append(f'{counter}. {sdisplay}')

        ccounter = 0
        if s.has_children:
            for child in s.childs.all():
                if not hide_percent:
                    sdisplay = str(child)
                else:
                    sdisplay = child.description

                ccounter += 1
                lines.append(f'&nbsp;&nbsp;&nbsp;&nbsp {counter}.{ccounter} {sdisplay}')

    return '\n'.join(lines)

def gen_row(curriculum_major, slots, admission_criteria, admission_project):
    major_cupt_code = curriculum_major.cupt_code
    
    r = []

    r.append(curriculum_major.faculty.title)
    r.append(major_cupt_code.display_title())
    r.append(str(slots))
    r.append('')
    r.append(render_score_criterias(admission_criteria.get_all_required_score_criteria(), short=True))
    r.append(render_score_criterias(admission_criteria.get_all_scoring_score_criteria(), True))
    r.append(f'{curriculum_major.faculty.id:02d}')
    r.append(major_cupt_code.program_type_code)
    r.append(major_cupt_code.program_code)
    r.append(major_cupt_code.major_code)

    return r

def row_key(row):
    return '-'.join(row[6:])

def sort_rows(rows):
    key_rows=[]
    c = 0
    for r in rows:
        key_rows.append((row_key(r),c,r))
        c += 1

    return [r[2] for r in sorted(key_rows)]

def main():
    csv_filename = sys.argv[1]
    project_ids = sys.argv[2:]

    is_empty_criteria = False
    is_slots_combined = False
    is_admission_2 = False
    is_no_add_limits = False
         
    while project_ids[0].startswith('--'):
        print(f'Option unknown: {project_ids[0]}')
        del project_ids[0]
    
    all_rows = []

    for project_id in project_ids:
        admission_project = AdmissionProject.objects.get(pk=project_id)

        faculties = Faculty.objects.all()
    
        admission_criterias = (AdmissionCriteria
                               .objects
                               .filter(admission_project_id=project_id,
                                       is_deleted=False)
                               .order_by('faculty_id'))

        project_rows = []
        row_criterias = []
        for admission_criteria in admission_criterias:
            curriculum_major_admission_criterias = admission_criteria.curriculummajoradmissioncriteria_set.select_related('curriculum_major').all()

            for mc in curriculum_major_admission_criterias:
                curriculum_major = mc.curriculum_major

                row_criteria = admission_criteria
                row = gen_row(curriculum_major, mc.slots, row_criteria, admission_project)
                project_rows.append(row)

        all_rows += project_rows
        
    all_rows = sort_rows(all_rows)

    major_counter = 0
    with open(csv_filename, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([''])
        writer.writerow(['''* เงื่อนไขขั้นต่ำ
* เกณฑ์การพิจารณาคัดเลือก'''])
        for r in all_rows:
            major_counter += 1
            writer.writerow([str(major_counter)] + r)

if __name__ == '__main__':
    main()
