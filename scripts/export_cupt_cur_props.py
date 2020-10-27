from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from appl.models import AdmissionProject, AdmissionRound, Faculty
from criteria.models import AdmissionCriteria

FIELDS = [
    'program_id',
    'major_id',
    'project_id',
    'project_name_th',
    'project_name_en',
    'type',
    'component_weight',
    'component_pat',
    'receive_student_number',
    'gender_male_number',
    'gender_female_number',
    'receive_add_limit',
    'join_id',
    'only_formal',
    'receive_student_number_formal ',
    'only_international',
    'receive_student_number_international ',
    'only_vocational',
    'receive_student_number_vocational',
    'only_non_formal',
    'receive_student_number_nonformal ',
    'min_height_male',
    'min_height_female',
    'min_weight_male',
    'min_weight_female',
    'max_weight_male',
    'max_weight_female',
    'min_hwr_male',
    'min_hwr_female',
    'min_bmi_male',
    'min_bmi_female',
    'max_bmi_male',
    'max_bmi_female',
    'min_r4_total_score',
    'min_gpax',
    'min_credit_gpa21',
    'min_credit_gpa22',
    'min_credit_gpa23',
    'min_credit_gpa24',
    'min_credit_gpa25',
    'min_credit_gpa26',
    'min_credit_gpa27',
    'min_credit_gpa28',
    'min_gpa21',
    'min_gpa22',
    'min_gpa23',
    'min_gpa24',
    'min_gpa25',
    'min_gpa26',
    'min_gpa27',
    'min_gpa28',
    'min_onet',
    'min_onet01',
    'min_onet02',
    'min_onet03',
    'min_onet04',
    'min_onet05',
    'min_gat',
    'min_gat1',
    'min_gat2',
    'min_pat1and2',
    'min_pat1',
    'min_pat2',
    'min_pat3',
    'min_pat4',
    'min_pat5',
    'min_pat6',
    'min_pat7_1',
    'min_pat7_2',
    'min_pat7_3',
    'min_pat7_4',
    'min_pat7_5',
    'min_pat7_6',
    'min_pat7_7',
    'min_9sub_09',
    'min_9sub_19',
    'min_9sub_29',
    'min_9sub_39',
    'min_9sub_49',
    'min_9sub_59',
    'min_9sub_69',
    'min_9sub_89',
    'min_9sub_99',
    'min_vnet_51',
    'min_vnet_511',
    'min_vnet_512',
    'min_vnet_513',
    'min_vnet_514',
    'min_bnet_393',
    'min_bnet_394',
    'min_inet_31',
    'min_inet_33',
    'min_inet_35',
    'min_inet_38',
    'min_nnet_421',
    'min_nnet_422',
    'min_nnet_423',
    'min_nnet_424',
    'min_nnet_425',
    'min_toefl_ibt',
    'min_toefl_pbt',
    'min_toefl_cbt',
    'min_toefl_ipt',
    'min_ielts',
    'min_toeic',
    'min_cutep',
    'min_tuget',
    'min_kept',
    'min_psutep',
    'min_kuept',
    'min_cmuetegs',
    'min_sat',
    'min_cefr  ',
    'min_ged_score',
    'min_gpa22_23',
    'description',
    'condition',
    'interview_location',
    'interview_date',
    'interview_time',
    'link',
]

DEFAULT_VALUES = {
    'condition': '',
    'interview_location': 'มหาวิทยาลัยเกษตรศาสตร์',
    'interview_date': '',
    'interview_time': '',
    'link': 'https://admission.ku.ac.th/',
}

PROJECT_TYPES = {
    'A0100': '1_2564',
    'A0200': '1_2564',
    'A0300': '1_2564',
    'A0400': '1_2564',
    'A0500': '1_2564',
    'A0600': '1_2564',
    'A0700': '1_2564',
    'A0800': '1_2564',
    'A0900': '1_2564',
    'A1000': '1_2564',
    'B1100': '2_2564',
    'B1200': '2_2564',
    'B1300': '2_2564',
    'B1400': '2_2564',
    'B1500': '2_2564',
    'B1600': '2_2564',
    'B1700': '2_2564',
    'B1800': '2_2564',
    'B1900': '2_2564',
    'B2000': '2_2564',
    'B2100': '2_2564',
    'B2200': '2_2564',
    'B2300': '2_2564',
    'B2400': '2_2564',
    'B2500': '2_2564',
    'B2600': '2_2564',
    'B0300': '2_2564',
    'C2700': '31_2564',
    'C2800': '32_2564',
}


def min_score_vector(admission_criteria):
    value_vectors = {}
    for f in FIELDS:
        if f.startswith('min') or f.startswith('max'):
            value_vectors[f] = 0

    return value_vectors

def gen_row(curriculum_major, slots, admission_criteria, admission_project):
    items = {}

    for k,v in DEFAULT_VALUES.items():
        items[k] = v
    
    score_items = min_score_vector(admission_criteria)
    for k,v in score_items.items():
        items[k] = v

    major_cupt_code = curriculum_major.cupt_code

    items['program_id'] = major_cupt_code.program_code
    items['major_id'] = major_cupt_code.major_code
    items['project_id'] = admission_project.cupt_code
    items['project_name_th'] = admission_project.short_title

    items['type'] = PROJECT_TYPES[admission_project.cupt_code]

    items['description'] = str(major_cupt_code)

    items['receive_student_number'] = slots
    items['receive_add_limit'] = 'A'
    
    ZERO_FIELDS = [
        'project_name_en',
        'gender_male_number',
        'gender_female_number',
        'component_weight',
        'component_pat',
        'join_id',
        'only_formal',
        'receive_student_number_formal ',
        'only_international',
        'receive_student_number_international ',
        'only_vocational',
        'receive_student_number_vocational',
        'only_non_formal',
        'receive_student_number_nonformal ',
    ]

    for f in ZERO_FIELDS:
        items[f] = 0

    return items
    
def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]
    csv_filename = sys.argv[3]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    faculties = Faculty.objects.all()
    
    admission_criterias = (AdmissionCriteria
                           .objects
                           .filter(admission_project_id=project_id,
                                   is_deleted=False)
                           .order_by('faculty_id'))

    rows = []
    
    for admission_criteria in admission_criterias:
        curriculum_major_admission_criterias = admission_criteria.curriculummajoradmissioncriteria_set.select_related('curriculum_major').all()

        for mc in curriculum_major_admission_criterias:
            curriculum_major = mc.curriculum_major

            row = gen_row(curriculum_major, mc.slots, admission_criteria, admission_project)

            rows.append(row)


    with open(csv_filename, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)

        writer.writeheader()
        for r in rows:
            writer.writerow(r)


if __name__ == '__main__':
    main()
