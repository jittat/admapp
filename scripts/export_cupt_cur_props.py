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

SLOTS_FIELD_NAME = 'receive_student_number'

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

SCORE_TYPE_TAGS = [
    #{ "score_type": "GPAX_5_SEMESTER", "description": "ผลการเรียนเฉลี่ยสะสม (GPAX) 5 ภาคเรียน", "unit": "" },
    { "score_type": "GPAX", "description": "ผลการเรียนเฉลี่ยสะสม (GPAX)", "unit": "" },
    { "score_type": "STUDY_AT_12", "description": "เป็นผู้ที่กำลังศึกษาอยู่ชั้นมัธยมศึกษาปีที่ 6 หรือเทียบเท่า", "unit": "" },
    { "score_type": "GRAD_OR_STUDY_AT_12", "description": "กำลังศึกษาหรือสำเร็จศึกษาชั้นมัธยมศึกษาปีที่ 6 หรือเทียบเท่า", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์", "unit": "" },
    { "score_type": "UNIT_FOREIGN", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้ภาษาต่างประเทศ", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์", "unit": "" },
    { "score_type": "ONET", "description": "O-NET (5 กลุ่มสาระวิชา)", "unit": "คะแนน" },
    { "score_type": "ONET_THA", "description": "O-NET (01) ภาษาไทย", "unit": "คะแนน" },
    { "score_type": "ONET_SOC", "description": "O-NET (02) สังคมศึกษา", "unit": "คะแนน" },
    { "score_type": "ONET_ENG", "description": "O-NET (03) ภาษาอังกฤษ", "unit": "คะแนน" },
    { "score_type": "ONET_MAT", "description": "O-NET (04) คณิตศาสตร์", "unit": "คะแนน" },
    { "score_type": "ONET_SCI", "description": "O-NET (05) วิทยาศาสตร์", "unit": "คะแนน" },
    { "score_type": "GAT", "description": "GAT", "unit": "คะแนน" },
    { "score_type": "GAT_1", "description": "GAT ส่วน 1", "unit": "คะแนน" },
    { "score_type": "GAT_2", "description": "GAT ส่วน 2", "unit": "คะแนน" },
    { "score_type": "PAT_1", "description": "PAT 1", "unit": "คะแนน" },
    { "score_type": "PAT_2", "description": "PAT 2", "unit": "คะแนน" },
    { "score_type": "PAT_3", "description": "PAT 3", "unit": "คะแนน" },
    { "score_type": "PAT_4", "description": "PAT 4", "unit": "คะแนน" },
    { "score_type": "PAT_5", "description": "PAT 5", "unit": "คะแนน" },
    { "score_type": "PAT_6", "description": "PAT 6", "unit": "คะแนน" },
    #{ "score_type": "PAT_7_1", "description": "PAT 7", "unit": "คะแนน" },
    { "score_type": "PAT_7_1", "description": "PAT 7.1", "unit": "คะแนน" },
    { "score_type": "PAT_7_2", "description": "PAT 7.2", "unit": "คะแนน" },
    { "score_type": "PAT_7_3", "description": "PAT 7.3", "unit": "คะแนน" },
    { "score_type": "PAT_7_4", "description": "PAT 7.4", "unit": "คะแนน" },
    { "score_type": "PAT_7_5", "description": "PAT 7.5", "unit": "คะแนน" },
    { "score_type": "PAT_7_6", "description": "PAT 7.6", "unit": "คะแนน" },
    { "score_type": "PAT_7_7", "description": "PAT 7.7", "unit": "คะแนน" },
    { "score_type": "TOEFL_PBT_ITP", "description": "TOEFL PBT/ITP", "unit": "คะแนน" },
    { "score_type": "TOEFL_CBT", "description": "TOEFL CBT", "unit": "คะแนน" },
    { "score_type": "TOEFL_IBT", "description": "TOEFL IBT", "unit": "คะแนน" },
    { "score_type": "IELTS", "description": "IELTS", "unit": "คะแนน" },
    { "score_type": "OOPT", "description": "OOPT", "unit": "คะแนน" },
    { "score_type": "KU_EPT", "description": "KU-EPT", "unit": "คะแนน" },
    { "score_type": "9SUB", "description": "วิชาสามัญ 9 วิชา", "unit": "คะแนน" },
    { "score_type": "UDAT_09", "description": "วิชาสามัญ ภาษาไทย (09)", "unit": "คะแนน" },
    { "score_type": "UDAT_19", "description": "วิชาสามัญ สังคมศึกษา (19)", "unit": "คะแนน" },
    { "score_type": "UDAT_29", "description": "วิชาสามัญ ภาษาอังกฤษ (29)", "unit": "คะแนน" },
    { "score_type": "UDAT_39", "description": "วิชาสามัญ คณิตศาสตร์ 1 (39)", "unit": "คะแนน" },
    { "score_type": "UDAT_49", "description": "วิชาสามัญ ฟิสิกส์ (49)", "unit": "คะแนน" },
    { "score_type": "UDAT_59", "description": "วิชาสามัญ เคมี (59)", "unit": "คะแนน" },
    { "score_type": "UDAT_69", "description": "วิชาสามัญ ชีววิทยา (69)", "unit": "คะแนน" },
    { "score_type": "UDAT_89", "description": "วิชาสามัญ คณิตศาสตร์ 2 (89)", "unit": "คะแนน" },
    { "score_type": "UDAT_99", "description": "วิชาสามัญ วิทยาศาสตร์ทั่วไป (99)", "unit": "คะแนน" },

    # HACK
    { "score_type": "GPAX", "description": "ผลการเรียนเฉลี่ยสะสม (GPAX) 6 ภาคเรียน", "unit": "" },
    { "score_type": "ONET_ENG", "description": "O-NET 03 ภาษาอังกฤษ", "unit": "คะแนน" },
    { "score_type": "ONET_MAT", "description": "O-NET (04) วิชาคณิตศาสตร์", "unit": "คะแนน" },
    { "score_type": "GAT", "description": "GAT85", "unit": "คะแนน" },
    { "score_type": "GAT", "description": "GAT ไม่ตำ่กว่า", "unit": "คะแนน" },
    { "score_type": "PAT_5", "description": "PAT 5 ไม่ต่ำกว่า", "unit": "คะแนน" },
    { "score_type": "UNIT_MATH", "description": "กลุ่มสาระการเรียนรู้คณิตศาสตร์", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ (แผนการเรียนวิทยาศาสตร์-คณิตศาสตร์)", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ (แผนการเรียนศิลป์คำนวณ)", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ ต้องเรียนรายวิชาพื้นฐานและรายวิชาเพิ่มเติม รวมกัน", "unit": "" },

    { "score_type": "UNIT_FOREIGN", "description": "กลุ่มสาระการเรียนรู้ภาษาต่างประเทศ", "unit": "" },
    { "score_type": "UNIT_FOREIGN", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้ภาษาต่างประเทศ (แผนการเรียนวิทยาศาสตร์-คณิตศาสตร์)", "unit": "" },

    { "score_type": "UNIT_SCI", "description": "กลุ่มสาระการเรียนรู้วิทยาศาสตร์", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ (แผนการเรียนวิทยาศาสตร์-คณิตศาสตร์)", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ (แผนการเรียนศิลป์คำนวณ)", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ ต้องเรียนรายวิชาพื้นฐานและรายวิชาเพิ่มเติม รวมกัน", "unit": "" },
    
    { "score_type": "GAT_2", "description": "GAT (ตอน 2 ภาษาอังกฤษ)", "unit": "คะแนน" },
    { "score_type": "GAT_2", "description": "GAT ตอน 2", "unit": "คะแนน" },
    { "score_type": "GAT_2", "description": "GAT ตอน2", "unit": "คะแนน" },
    { "score_type": "GPAX", "description": "ผลการเรียนเฉลี่ยสะสม (GPAX) 5 ภาคเรียน", "unit": "" },
    { "score_type": "UDAT_09", "description": "วิชา 09", "unit": "คะแนน" },
    { "score_type": "UDAT_19", "description": "วิชา 19", "unit": "คะแนน" },
    { "score_type": "UDAT_29", "description": "วิชา 29", "unit": "คะแนน" },
    { "score_type": "UDAT_39", "description": "วิชา 39", "unit": "คะแนน" },
    { "score_type": "UDAT_49", "description": "วิชา 49", "unit": "คะแนน" },
    { "score_type": "UDAT_59", "description": "วิชา 59", "unit": "คะแนน" },
    { "score_type": "UDAT_69", "description": "วิชา 69", "unit": "คะแนน" },
    { "score_type": "UDAT_89", "description": "วิชา 89", "unit": "คะแนน" },
    { "score_type": "UDAT_99", "description": "วิชา 99", "unit": "คะแนน" },
]

SCORE_TYPE_REVERSE_MAP = dict([
    (t['description'].strip(), t['score_type'].strip())
    for t in SCORE_TYPE_TAGS
])

SCORE_TYPE_FIELD_MAP = {
    "GPAX_5_SEMESTER": 'ERROR',
    "GPAX": "min_gpax",
    "UNIT_MATH": 'min_credit_gpa22',
    "UNIT_FOREIGN": 'min_credit_gpa28',
    "UNIT_SCI": 'min_credit_gpa23',
    "ONET": 'min_onet',
    "ONET_THA": 'min_onet01',
    "ONET_SOC": 'min_onet02',
    "ONET_ENG": 'min_onet03',
    "ONET_MAT": 'min_onet04',
    "ONET_SCI": 'min_onet05',
    "GAT": 'min_gat',
    "GAT_1": 'min_gat1',
    "GAT_2": 'min_gat2',
    "PAT_1": 'min_pat1',
    "PAT_2": 'min_pat2',
    "PAT_3": 'min_pat3',
    "PAT_4": 'min_pat4',
    "PAT_5": 'min_pat5',
    "PAT_6": 'min_pat6',
    "PAT_7_1": 'min_pat7_1',
    "PAT_7_2": 'min_pat7_2',
    "PAT_7_3": 'min_pat7_3',
    "PAT_7_4": 'min_pat7_4',
    "PAT_7_5": 'min_pat7_5',
    "PAT_7_6": 'min_pat7_6',
    "PAT_7_7": 'min_pat7_7',
    "UDAT_09": 'min_9sub_09',
    "UDAT_19": 'min_9sub_19',
    "UDAT_29": 'min_9sub_29',
    "UDAT_39": 'min_9sub_39',
    "UDAT_49": 'min_9sub_49',
    "UDAT_59": 'min_9sub_59', 
    "UDAT_69": 'min_9sub_69',
    "UDAT_89": 'min_9sub_89',
    "UDAT_99": 'min_9sub_99',
}

def reverse_score_type(score_criteria):
    if score_criteria.score_type != 'OTHER':
        return score_criteria.score_type
    elif score_criteria.description.strip() in SCORE_TYPE_REVERSE_MAP:
        return SCORE_TYPE_REVERSE_MAP[score_criteria.description.strip()]
    else:
        return 'OTHER'

all_missing_descriptions = []
    
def min_score_vector(admission_criteria, curriculum_major):
    value_vectors = {}
    for f in FIELDS:
        if f.startswith('min') or f.startswith('max'):
            value_vectors[f] = 0

    if not admission_criteria:
        return value_vectors

    is_error = False
    score_criterias = []
    for c in admission_criteria.get_all_required_score_criteria():
        if c.has_children():
            if c.relation != 'AND':
                print('Error type:', c.relation)
                for child in c.childs.all():
                    print(f"    - {child}")
                is_error = True
            else:
                for child in c.childs.all():
                    score_criterias.append(child)
        else:
            score_criterias.append(c)        

    for c in score_criterias:
        score_type = c.score_type
        if score_type == 'OTHER':
            score_type = reverse_score_type(c)
        if c.value != None and c.value > 0:
            if score_type not in SCORE_TYPE_FIELD_MAP:
                print(f'Error missing {score_type} {c} "{c.description.strip()}"')
                all_missing_descriptions.append(c.description)
                is_error = True
            elif SCORE_TYPE_FIELD_MAP[score_type] == 'ERROR':
                #print('Found:', score_type, c)
                print('Error gpax5', c)
                is_error = True
            else:
                value_vectors[SCORE_TYPE_FIELD_MAP[score_type]] = float(c.value)

    if is_error:
        print('=============', curriculum_major.faculty, '==========', curriculum_major.cupt_code)
                
    return value_vectors

def gen_row(curriculum_major, slots, admission_criteria, admission_project):
    items = {}

    for k,v in DEFAULT_VALUES.items():
        items[k] = v
    
    score_items = min_score_vector(admission_criteria, curriculum_major)
    for k,v in score_items.items():
        items[k] = v

    major_cupt_code = curriculum_major.cupt_code

    items['program_id'] = major_cupt_code.program_code
    items['major_id'] = major_cupt_code.major_code
    items['project_id'] = admission_project.cupt_code
    items['project_name_th'] = admission_project.short_title

    items['type'] = PROJECT_TYPES[admission_project.cupt_code]

    items['description'] = f'{curriculum_major.faculty} {major_cupt_code}'

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

def row_key(row, short_project_id=False):
    if short_project_id:
        return f"{row['project_id'][:3]}-{row['program_id']}-{row['major_id']}"
    else:
        return f"{row['project_id']}-{row['program_id']}-{row['major_id']}"

def sort_rows(rows):
    key_rows=[]
    c = 0
    for r in rows:
        key_rows.append((row_key(r, True),c,r))
        c += 1

    return [r[2] for r in sorted(key_rows)]

def combine_slots(project_rows):
    total_slots = {}

    for r in project_rows:
        k = row_key(r)
        if k not in total_slots:
            total_slots[k] = 0
        else:
            pass
            # print(f'Dup {r}')
        total_slots[k] += r[SLOTS_FIELD_NAME]

    reported = set()
    output_project_rows = []
    for r in project_rows:
        k = row_key(r)

        if k in reported:
            continue

        new_row = dict(r)
        new_row[SLOTS_FIELD_NAME] = total_slots[k]
        output_project_rows.append(new_row)
        
        reported.add(k)
        
    return output_project_rows

def update_project_id(old_project_id, counter):
    return old_project_id[:3] + ('%02d' % (counter,))

def mark_multiline_majors(project_rows, row_criterias):
    key_counts = {}
    for r in project_rows:
        k = row_key(r)
        if k not in key_counts:
            key_counts[k] = 0
        key_counts[k] += 1

    project_id_counter = {}
    for r,c in zip(project_rows, row_criterias):
        k = row_key(r)
        if key_counts[k] > 1:
            if k not in project_id_counter:
                project_id_counter[k] = 0
            else:
                project_id_counter[k] += 1
                r['project_id'] = update_project_id(r['project_id'], project_id_counter[k])
            
            if c.additional_description != '':
                r['description'] += f' {c.additional_description}'
            else:
                r['description'] += f' (#{c.id})'

            if c.additional_condition != '':
                r['condition'] += f'{c.additional_condition}'
            else:
                r['condition'] += f'(#{c.id})'

def mark_join_ids(project_rows, join_id_base):
    key_slots = {}
    for r in project_rows:
        k = row_key(r)
        if k not in key_slots:
            key_slots[k] = []
        key_slots[k].append(r['receive_student_number'])

        if len(key_slots[k]) > 1:
            if ((len([s for s in key_slots[k] if s == 0]) > 0) and
                (len([s for s in key_slots[k] if s > 0]) > 1)):
                print('ERROR too many receive_student_number', r)

    key_join_ids = {}
    jcount = 0
    
    for r in project_rows:
        if r['receive_student_number'] == 0:
            k = row_key(r)
            if len(key_slots[k]) <= 1:
                print('ZERO receive_student_number', r)
            else:
                if k not in key_join_ids:
                    jcount += 1
                    join_id = join_id_base + jcount
                    key_join_ids[k] = join_id
                    
    for r in project_rows:
        k = row_key(r)
        if k in key_join_ids:
            r['join_id'] = key_join_ids[k]
            if r['receive_student_number'] == 0:
                slots = [s for s in key_slots[k] if s > 0][0]
                r['receive_student_number'] = slots
                
                
def main():
    csv_filename = sys.argv[1]
    project_ids = sys.argv[2:]

    is_empty_criteria = False
    is_slots_combined = False
         
    while project_ids[0].startswith('--'):
        if project_ids[0] == '--empty':
            is_empty_criteria = True
        elif project_ids[0] == '--combine':
            is_slots_combined = True
        else:
            print(f'Option unknown: {project_ids[0]}')
        del project_ids[0]
    
    rows = []

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
                if is_empty_criteria:
                    row_criteria = None
                
                row = gen_row(curriculum_major, mc.slots, row_criteria, admission_project)

                project_rows.append(row)
                row_criterias.append(row_criteria)

        if is_slots_combined:
            project_rows = combine_slots(project_rows)
        else:
            mark_join_ids(project_rows, int(project_id)*100)
            mark_multiline_majors(project_rows, row_criterias)
        
        rows += project_rows

    for d in set(all_missing_descriptions):
        print(d.strip())
        
    rows = sort_rows(rows)
    
    with open(csv_filename, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)

        writer.writeheader()
        for r in rows:
            writer.writerow(r)


if __name__ == '__main__':
    main()
