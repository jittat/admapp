from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from appl.models import AdmissionProject, AdmissionRound, Faculty
from criteria.models import AdmissionCriteria

FIELDS_STR = """
program_id
major_id
project_id
project_name_th
project_name_en
type
receive_student_number
gender_male_number
gender_female_number
receive_add_limit
join_id
only_formal
only_international
only_vocational
only_non_formal
only_ged
min_priority
min_age
min_age_date
max_age
max_age_date
min_height_male
min_height_female
min_weight_male
min_weight_female
max_weight_male
max_weight_female
min_bmi_male
min_bmi_female
max_bmi_male
max_bmi_female
min_gpax
min_credit_gpa21
min_credit_gpa22
min_credit_gpa23
min_credit_gpa24
min_credit_gpa25
min_credit_gpa26
min_credit_gpa27
min_credit_gpa28
min_credit_gpa29
min_gpa21
min_gpa22
min_gpa23
min_gpa24
min_gpa25
min_gpa26
min_gpa27
min_gpa28
min_gpa29
min_gpa22_23
min_credit_gpa22_23
min_gpa22_23_28
min_credit_gpa22_23_28
grad_current
gatpat_current
min_gat
min_gat1
min_gat2
min_pat1_pat2
min_pat1
min_pat2
min_pat3
min_pat4
min_pat5
min_pat6
min_pat7
min_pat7_1
min_pat7_2
min_pat7_3
min_pat7_4
min_pat7_5
min_pat7_6
min_pat7_7
min_9sub_sum
min_9sub_09
min_9sub_19
min_9sub_29
min_9sub_39
min_9sub_49
min_9sub_59
min_9sub_69
min_9sub_89
min_9sub_99
min_vnet_51
min_vnet_511
min_vnet_512
min_vnet_513
min_vnet_514
min_toefl_ibt
min_toefl_pbt
min_toefl_cbt
min_toefl_itp
min_ielts
min_toeic
min_cutep
min_tuget
min_kept
min_psutep
min_kuept
min_cmuetegs
min_swu_set
min_det
min_sat
min_cefr
min_ged_score
description
condition
interview_location
interview_date
interview_time
link
min_cotmes_01
min_cotmes_02
min_cotmes_03
min_mu001
min_mu002
min_mu003
min_su001
min_su002
min_su003
min_su004
min_tu001
min_tu002
min_tu003
min_tu004
min_tu005
min_tu061
min_tu062
min_tu071
min_tu072
min_tu081
min_tu082
min_tu091
min_tu092
min_gsat
min_gsat_l
min_gsat_m
min_mu_elt
min_netsat_math
min_netsat_lang
min_netsat_sci
min_netsat_phy
min_netsat_chem
min_netsat_bio
score_condition
subject_names
score_minimum
"""

FIELDS = FIELDS_STR.strip().split()

SLOTS_FIELD_NAME = 'receive_student_number'

DEFAULT_VALUES = {
    'only_formal': 1,
    'only_international': 1,
    'only_non_formal': 1,
    'only_vocational': 1,
    'only_ged': 1,
    'condition': '',
    'interview_location': 'มหาวิทยาลัยเกษตรศาสตร์',
    'interview_date': '',
    'interview_time': '',
    'link': 'https://admission.ku.ac.th/',
    'score_condition': 0,
    'subject_names': 0,
    'score_minimum': 0,
}

PROJECT_TYPES = {
    'A0100': '1_2565',
    'A0200': '1_2565',
    'A0300': '1_2565',
    'A0400': '1_2565',
    'A0500': '1_2565',
    'A0599': '1_2565',
    'A0600': '1_2565',
    'A0699': '1_2565',
    'A0700': '1_2565',
    'A0799': '1_2565',
    'A0700': '1_2565',
    'A0800': '1_2565',
    'A0900': '1_2565',
    'A1000': '1_2565',
    'B1100': '2_2565',
    'B1200': '2_2565',
    'B1300': '2_2565',
    'B1400': '2_2565',
    'B1500': '2_2565',
    'B1600': '2_2565',
    'B1700': '2_2565',
    'B1800': '2_2565',
    'B1900': '2_2565',
    'B2000': '2_2565',
    'B2100': '2_2565',
    'B2200': '2_2565',
    'B2300': '2_2565',
    'B2400': '2_2565',
    'B2500': '2_2565',
    'B2600': '2_2565',
    'B2700': '2_2565',
    'B2799': '2_2565',
    'C2800': '3_2565',
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
    { "score_type": "GPAX", "description": "ผลการเรียนเฉลี่ยสะสม (GPAX) ไม่ต่ำกว่า", "unit": "" },
    { "score_type": "ONET_ENG", "description": "O-NET 03 ภาษาอังกฤษ", "unit": "คะแนน" },
    { "score_type": "ONET_ENG", "description": "O-NET (03)", "unit": "คะแนน" },
    { "score_type": "ONET_ENG", "description": "O-NET (03) ภาษาอังกฤษ ไม่ต่ำกว่า", "unit": "คะแนน" },
    { "score_type": "ONET_MAT", "description": "O-NET (04) วิชาคณิตศาสตร์", "unit": "คะแนน" },
    { "score_type": "GAT", "description": "GAT85", "unit": "คะแนน" },
    { "score_type": "GAT", "description": "GAT ไม่ตำ่กว่า", "unit": "คะแนน" },
    { "score_type": "GAT", "description": "GAT (85): วิชาความถนัดทั่วไป", "unit": "คะแนน" },
    { "score_type": "PAT_1", "description": "PAT I ความถนัดทางคณิตศาสตร์", "unit": "คะแนน" },
    { "score_type": "PAT_1", "description": "PAT1 (71): วิชาความถนัดทางคณิตศาสตร์", "unit": "คะแนน" },
    { "score_type": "PAT_2", "description": "PAT2 (72): วิชาความถนัดทางวิทยาศาสตร์", "unit": "คะแนน" },
    { "score_type": "PAT_5", "description": "PAT 5 ไม่ต่ำกว่า", "unit": "คะแนน" },
    { "score_type": "UNIT_MATH", "description": "กลุ่มสาระการเรียนรู้คณิตศาสตร์", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ (แผนการเรียนวิทยาศาสตร์-คณิตศาสตร์)", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ (แผนการเรียนศิลป์คำนวณ)", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ ไม่น้อยกว่า", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ ต้องเรียนรายวิชาพื้นฐานและรายวิชาเพิ่มเติม รวมกัน", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ (แผนการเรียนศิลป์คำนวณ) ไม่ต่ำกว่า 12.00", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ ต้องเรียนรายวิชาพื้นฐานและรายวิชาเพิ่มเติมรวมกัน", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ ต้องเรียนรายวิชาพิ้นฐานและรายวิชาเพิ่มเติม รวมกัน", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้คณิตศาสตร์ ไม่น้อยกว่า", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "หน่วยกิจกลุ่มสาระคณิตศาสตร์", "unit": "" },
    { "score_type": "UNIT_MATH", "description": "หน่วยกิตกลุ่มสาระคณิตศาสตร์", "unit": "" },

    { "score_type": "UNIT_FOREIGN", "description": "กลุ่มสาระการเรียนรู้ภาษาต่างประเทศ", "unit": "" },
    { "score_type": "UNIT_FOREIGN", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้ภาษาต่างประเทศ (แผนการเรียนวิทยาศาสตร์-คณิตศาสตร์)", "unit": "" },
    { "score_type": "UNIT_FOREIGN", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้ภาษาต่างประเทศ (ภาษาอังกฤษ)", "unit": "" },
    { "score_type": "UNIT_FOREIGN", "description": "หน่วยกิจกลุ่มสาระภาษาต่างประเทศ", "unit": "" },
    { "score_type": "UNIT_FOREIGN", "description": "หน่วยกิตกลุ่มสาระภาษาต่างประเทศ", "unit": "" },

    { "score_type": "UNIT_SCI", "description": "กลุ่มสาระการเรียนรู้วิทยาศาสตร์", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ (แผนการเรียนวิทยาศาสตร์-คณิตศาสตร์)", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ (แผนการเรียนศิลป์คำนวณ)", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ ไม่น้อยกว่า", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ ต้องเรียนรายวิชาพื้นฐานและรายวิชาเพิ่มเติม รวมกัน", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ ต้องเรียนรายวิชาพื้นฐานและรายวิชาเพิ่มเติมรวมกัน", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ ต้องเรียนวิชาพื้นฐานและรายวิชาเพิ่มเติม รวมกัน", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "เรียนรายวิชาในกลุ่มสาระการเรียนรู้วิทยาศาสตร์ ไม่น้อยกว่า", "unit": "" },
    { "score_type": "UNIT_SCI", "description": "หน่วยกิตกลุ่มสาระวิทยาศาสตร์", "unit": "" },

    { "score_type": "GPAX_SCI", "description": "คะแนนเฉลี่ยรายวิชากลุ่มสาระการเรียนรู้วิทยาศาสตร์", "unit": "" },
    { "score_type": "GPAX_MATH", "description": "คะแนนเฉลี่ยรายวิชากลุ่มสาระการเรียนรู้คณิตศาสตร์", "unit": "" },
    { "score_type": "GPAX_FOREIGN", "description": "คะแนนเฉลี่ยรายวิชากลุ่มสาระการเรียนรู้ภาษาต่างประเทศ", "unit": "" },
    
    { "score_type": "GAT_2", "description": "GAT (ตอน 2 ภาษาอังกฤษ)", "unit": "คะแนน" },
    { "score_type": "GAT_2", "description": "GAT ตอน 2", "unit": "คะแนน" },
    { "score_type": "GAT_2", "description": "GAT ตอน2", "unit": "คะแนน" },
    { "score_type": "GAT_2", "description": "GAT General (English)", "unit": "คะแนน" },

    { "score_type": "GPAX", "description": "ผลการเรียนเฉลี่ยสะสม (GPAX) 5 ภาคเรียน", "unit": "" },
    { "score_type": "UDAT_09", "description": "วิชา 09", "unit": "คะแนน" },
    { "score_type": "UDAT_19", "description": "วิชา 19", "unit": "คะแนน" },
    { "score_type": "UDAT_29", "description": "วิชา 29", "unit": "คะแนน" },
    { "score_type": "UDAT_29", "description": "29", "unit": "คะแนน" },
    { "score_type": "UDAT_39", "description": "วิชา 39", "unit": "คะแนน" },
    { "score_type": "UDAT_49", "description": "วิชา 49", "unit": "คะแนน" },
    { "score_type": "UDAT_59", "description": "วิชา 59", "unit": "คะแนน" },
    { "score_type": "UDAT_69", "description": "วิชา 69", "unit": "คะแนน" },
    { "score_type": "UDAT_89", "description": "วิชา 89", "unit": "คะแนน" },
    { "score_type": "UDAT_99", "description": "วิชา 99", "unit": "คะแนน" },


    # HACK ad1
    { "score_type": 'CW701', 'description': '7 (รูปแบบที่ 1): **** ยังไม่ได้เลือก PAT **** กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 1)' },
    { "score_type": 'CW701', 'description': '7 (รูปแบบที่ 1) กลุ่ม 7 ครุศาสตร์ ศึกษาศาสตร์ พลศึกษา สุขศึกษา (รูปแบบที่ 1)' },
    { "score_type": 'CW140', 'description': '1.4: กลุ่ม 1 วิทยาศาสตร์สุขภาพ - สัตวแพทย์ศาสตร์' },
    { "score_type": 'CW110', 'description': '1.1: กลุ่ม 1 วิทยาศาสตร์สุขภาพ - สัตวแพทย์ศาสตร์ สหเวชศาสตร์ สาธารณสุขศาสตร์ เทคนิคการแพทย์ พยาบาลศาสตร์ วิทยาศาสตร์การกีฬา' },

    { "score_type": 'MIN_GPA21', 'description': 'ผลการเรียนเฉลี่ยรวมของกลุ่มสาระการเรียนรู้ภาษาไทย'},
    { "score_type": 'MIN_GPA22', 'description': 'คะแนนเฉลี่ยกลุ่มสาระคณิตศาสตร์'},
    { "score_type": 'MIN_GPA22', 'description': 'มีคะแนนเฉลี่ยกลุ่มสาระคณิตศาสตร์'},
    { "score_type": 'MIN_GPA22', 'description': 'ผลการเรียนกลุ่มสาระการเรียนรู้คณิตศาสตร์'},
    { "score_type": 'MIN_GPA22', 'description': 'คะแนนเฉลี่ยต่ำสุดของกลุ่มสาระการเรียนรู้คณิตศาสตร์'},
    { "score_type": 'MIN_GPA23', 'description': 'คะแนนเฉลี่ยกลุ่มสาระวิทยาศาสตร์'},
    { "score_type": 'MIN_GPA23', 'description': 'มีคะแนนเฉลี่ยกลุ่มสาระวิทยาศาสตร์'},
    { "score_type": 'MIN_GPA23', 'description': 'ผลการเรียนกลุ่มสาระการเรียนรู้วิทยาศาสตร์'},
    { "score_type": 'MIN_GPA23', 'description': 'คะแนนเฉลี่ยต่ำสุดในกลุ่มสาระการเรียนรู้วิทยาศาสตร์'},
    { "score_type": 'MIN_GPA28', 'description': 'มีคะแนนเฉลี่ยกลุ่มสาระภาษาต่างประเทศ'},
    { "score_type": 'MIN_GPA28', 'description': 'ผลการเรียนเฉลี่ยรวมของกลุ่มสาระการเรียนรู้ภาษาต่างประเทศ'},
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
    "GPAX_MATH": 'min_gpa22',
    "GPAX_FOREIGN": 'min_gpa28',
    "GPAX_SCI": 'min_gpa23',
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

    "MIN_GPA21": 'min_gpa21',
    "MIN_GPA22": 'min_gpa22',
    "MIN_GPA23": 'min_gpa23',
    "MIN_GPA28": 'min_gpa28',

    "VNET": 'min_vnet_51',
    "PAT_7": 'min_pat7',
}

ADD_LIMITS_CONFIG = ""
OLD_ADD_LIMITS_CONFIG = """C3	10020222900201A		C2700
C3	10020222902501A		C2700
C10	10020222902501B		C2700
C3	10020222900201A		C2800
C1	10020222902501A		C2800
C3	10020222902501B		C2800
C5	10020108901001A		C2700
C5	10020108901001B		C2700
C5	10020108901001A		C2800
C5	10020108901001A		C2800
C5	10020108901001A		C2800
C5	10020108901001A		C2800
C5	10020108901001A		C2800
C5	10020108901001A		C2800
C5	10020108901001B		C2800
C5	10020108901001B		C2800
C5	10020108901001B		C2800
C5	10020108901001B		C2800
C5	10020108901001B		C2800
C5	10020108901001B		C2800
C5	10020101111801A		C2800
C5	10020101500101A		C2800
C5	10020101500201A		C2800
C5	10020101500202A		C2800
C5	10020101500203A		C2800
C5	10020101500204A		C2800
C5	10020101500205A		C2800
C5	10020101500205E		C2800
C5	10020101500301A		C2800
C5	10020101111801A		C2700
C5	10020101500101A		C2700
C5	10020101500201A		C2700
C5	10020101500202A		C2700
C5	10020101500203A		C2700
C5	10020101500204A		C2700
C5	10020101500205A		C2700
C5	10020101500205E		C2700
C5	10020101500301A		C2700
"""

ADD_LIMITS = dict({
    (i[3],i[1],i[2]): i[0] for i in [l.strip().split("\t") for l in ADD_LIMITS_CONFIG.split("\n")] if len(i) == 4
})

ADDITIONAL_FIELD_VALUES = {
}

def reverse_score_type(score_criteria):
    if score_criteria.score_type != 'OTHER':
        return score_criteria.score_type
    elif score_criteria.description.strip() in SCORE_TYPE_REVERSE_MAP:
        return SCORE_TYPE_REVERSE_MAP[score_criteria.description.strip()]
    else:
        return 'OTHER'

all_missing_descriptions = []

def print_error_line(prefix, curriculum_major):
    print(prefix, '^^ =============', curriculum_major.faculty, '==========', 
          curriculum_major.cupt_code,
          curriculum_major.admission_project.id,
          curriculum_major.cupt_code.get_program_major_code())

    
def normalize_score_type(c):
    is_error = False
    
    score_type = c.score_type
    if score_type == 'OTHER':
        score_type = reverse_score_type(c)
    if score_type not in SCORE_TYPE_FIELD_MAP:
        print(f'Error missing {score_type} {c} "{c.description.strip()}"')
        is_error = True
    elif SCORE_TYPE_FIELD_MAP[score_type] == 'ERROR':
        #print('Found:', score_type, c)
        print('Error gpax5', c.score_type, score_type, c, c.description.strip())
        is_error = True
    return score_type, is_error


def min_score_vector_from_criterias(score_criterias, curriculum_major):
    value_vectors = {}
    for f in FIELDS:
        if f.startswith('min') or f.startswith('max'):
            value_vectors[f] = 0

    if score_criterias == []:
        return value_vectors
            
    is_error = False
    for c in score_criterias:
        score_type, this_error = normalize_score_type(c)

        if c.value != None and c.value > 0:
            if not this_error:
                value_vectors[SCORE_TYPE_FIELD_MAP[score_type]] = float(c.value)
            else:
                all_missing_descriptions.append(c.description)
                is_error = True
        else:
            if score_type == 'OTHER':
                is_error = True
                print(f'OTHER - None: Error missing {score_type} {c} "{c.description.strip()}"')
                
    if is_error:
        print_error_line('4', curriculum_major)
                
    return value_vectors

def build_or_conditions(or_criterias):
    items = {}
    items['score_condition'] = 1
    names = []
    scores = []
    for c in or_criterias:
        score_type, this_error = normalize_score_type(c)
        if not this_error:
            names.append(SCORE_TYPE_FIELD_MAP[score_type])
            scores.append(float(c.value))
        else:
            print(f'OR error {score_type} {c} "{c.description.strip()}"')
        
    items['subject_names'] = ' '.join(names)
    items['score_minimum'] = ' '.join([str(s) for s in scores])
    print('OR built:', items)
    return items

def min_score_vectors(admission_criteria, curriculum_major):
    if not admission_criteria:
        return [min_score_vector_from_criterias([], curriculum_major)]

    or_count = 0
    or_criterias = []
    
    is_error = False
    score_criterias = []
    for c in admission_criteria.get_all_required_score_criteria():
        if c.has_children():
            if c.relation != 'AND':
                if c.relation == 'OR':
                    or_count += 1
                    for child in c.childs.all():
                        or_criterias.append(child)
                if (or_count > 1) or (c.relation != 'OR'):
                    print('Error type (or too many OR):', c.relation)
                    for child in c.childs.all():
                        print(f"    - {child}")
                    is_error = True
            else:
                for child in c.childs.all():
                    score_criterias.append(child)
        else:
            score_criterias.append(c)        

    if or_count == 0:
        value_vectors = min_score_vector_from_criterias(score_criterias, curriculum_major)
    
        if is_error:
            print_error_line('1', curriculum_major)

        return [value_vectors]
    elif or_count == 1:
        print('OR found:', curriculum_major.cupt_code, curriculum_major.admission_project.id, curriculum_major.cupt_code.get_program_major_code(), ':', or_criterias)
        output = []
        
        value_vectors = min_score_vector_from_criterias([c for c in score_criterias], curriculum_major)

        or_conditions = build_or_conditions(or_criterias)
        value_vectors.update(or_conditions)

        output.append(value_vectors)
            
        if is_error:
            print_error_line('2', curriculum_major)

        return output

    else:
        value_vectors = min_score_vector_from_criterias(score_criterias, curriculum_major)
    
        if is_error:
            print_error_line('3 TOO MANY ORs ', curriculum_major)
                
        return [value_vectors]

from export_major_criterias_as_json import score_vector_from_criterias

def gen_rows(curriculum_major, slots, admission_criteria, admission_project, json_data=None):
    score_items_list = min_score_vectors(admission_criteria, curriculum_major)

    rows = []

    first_row = True
    for score_items in score_items_list:
        items = {}

        for k,v in DEFAULT_VALUES.items():
            items[k] = v

        for k,v in score_items.items():
            items[k] = v

        major_cupt_code = curriculum_major.cupt_code

        items['program_id'] = major_cupt_code.program_code
        items['major_id'] = major_cupt_code.major_code
        items['project_id'] = admission_project.cupt_code
        items['project_name_th'] = admission_project.short_title

        items['type'] = PROJECT_TYPES[admission_project.cupt_code]

        items['description'] = f'{curriculum_major.faculty} {major_cupt_code}'

        if admission_criteria and admission_criteria.additional_condition != '':
            items['condition'] = admission_criteria.additional_condition

        if first_row:
            items['receive_student_number'] = slots
        else:
            items['receive_student_number'] = 0
            
        items['receive_add_limit'] = 'A'
    
        ZERO_FIELDS = [
            'project_name_en',
            'gender_male_number',
            'gender_female_number',
            'join_id',
        ]
        
        for f in ZERO_FIELDS:
            if f not in items:
                items[f] = 0

        additional_field_value_key = (admission_project.id,) + curriculum_major.cupt_code.get_program_major_code()
        if additional_field_value_key in ADDITIONAL_FIELD_VALUES:
            for f in ADDITIONAL_FIELD_VALUES[additional_field_value_key]:
                items[f] = ADDITIONAL_FIELD_VALUE_KEY[additional_field_value_key][f]
            
        rows.append(items)

        if json_data != None:
            json_data.append({
                'row': items,
                'scoring_criterias': score_vector_from_criterias(admission_criteria, curriculum_major)
            })

        first_row = False

    return rows

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

            if c!=None:
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
            print(k)
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

def update_component_weight(row, admission_criteria, curriculum_major):
    score_criterias = []
    is_error = False
    is_assigned = False
    
    for c in admission_criteria.get_all_scoring_score_criteria():
        if c.has_children():
            print('Error type:', c.relation)
            for child in c.childs.all():
                print(f"    - {child}")
                is_error = True
        else:
            score_criterias.append(c)        

    if len(score_criterias) != 1:
        print('Too many', len(score_criterias))
        is_error = True
        
    for c in score_criterias:
        score_type = c.score_type
        if score_type == 'OTHER':
            score_type = reverse_score_type(c)

        else:
            print('Unknown scoring', c)
            is_error = True

    if not is_assigned:
        print('ERROR not assigned')
        
    if is_error or (not is_assigned):
        print("----------------", curriculum_major.cupt_code)

def set_add_limits(row, admission_project):
    k = (admission_project.cupt_code, row['program_id'], row['major_id'])
    if k in ADD_LIMITS:
        #print('update add limits', k, ADD_LIMITS[k])
        row['receive_add_limit'] = ADD_LIMITS[k]

def project_id_male_acceptance_update(r):
    r['project_id'] = r['project_id'][:3] + '99'
    r['project_name_th'] += '_รับเพศชาย'
    return r
        
POST_PROCESSORS = {
    'male': project_id_male_acceptance_update,
}

def post_process(project_rows, post_processors):
    if len(post_processors) != 0:
        rows = []
        for r in project_rows:
            for f in post_processors:
                r = f(r)
            rows.append(r)
        project_rows = rows
    return project_rows

    
def filter_keywords(admission_criterias,
                    inclusion_keywords,
                    exclusion_keywords):
    if len(inclusion_keywords) != 0:
        admission_criterias = [a for a in admission_criterias if a.required_score_criteria_includes(inclusion_keywords)]
    if len(exclusion_keywords) != 0:
        admission_criterias = [a for a in admission_criterias if a.required_score_criteria_exclude(exclusion_keywords)]
    return admission_criterias

def export_json(scoring_json_filename, json_data):

    def filter_row_data_for_json(r):
        F = [
            'program_id',
            'project_id',
            'major_id',
            'description',
        ]
        return {
            f: r[f]
            for f in F
        }

    import json

    data = []
    for d in json_data:
        data.append({
            'row': filter_row_data_for_json(d['row']),
            'scoring_criterias': d['scoring_criterias'],
        })
    
    with open(scoring_json_filename,'w') as f:
        f.write(json.dumps(data, indent=1))


def main():
    csv_filename = sys.argv[1]
    project_ids = sys.argv[2:]

    is_empty_criteria = False
    is_slots_combined = False
    is_admission_2 = False
    is_no_add_limits = False
    inclusion_keywords = []
    exclusion_keywords = []

    post_processors = []

    scoring_json_filename = None
    
    while project_ids[0].startswith('--'):
        if project_ids[0] == '--empty':
            is_empty_criteria = True
        elif project_ids[0] == '--combine':
            is_slots_combined = True
        elif project_ids[0] == '--ad2':
            is_admission_2 = True
        elif project_ids[0] == '--r12':
            is_no_add_limits = True
        elif project_ids[0] == '--include':
            inclusion_keywords = project_ids[1].split(',')
            #print('Include:', inclusion_keywords)
            del project_ids[0]
        elif project_ids[0] == '--exclude':
            exclusion_keywords = project_ids[1].split(',')
            #print('Exclude:', exclusion_keywords)
            del project_ids[0]
        elif project_ids[0] == '--postprocessing':
            for f in project_ids[1].split(','):
                post_processors.append(POST_PROCESSORS[f])
            del project_ids[0]
        elif project_ids[0] == '--json':
            scoring_json_filename = project_ids[1]
            del project_ids[0]
        else:
            print(f'Option unknown: {project_ids[0]}')
        del project_ids[0]
    
    all_rows = []
    json_data = []
    
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

        admission_criterias = filter_keywords(admission_criterias,
                                              inclusion_keywords,
                                              exclusion_keywords)
        
        for admission_criteria in admission_criterias:
            curriculum_major_admission_criterias = admission_criteria.curriculummajoradmissioncriteria_set.select_related('curriculum_major').all()

            for mc in curriculum_major_admission_criterias:
                curriculum_major = mc.curriculum_major

                row_criteria = admission_criteria
                if is_empty_criteria:
                    row_criteria = None
                
                rows = gen_rows(curriculum_major, mc.slots, row_criteria, admission_project, json_data)

                for row in rows:
                    set_add_limits(row, admission_project)
                    if is_admission_2:
                        update_component_weight(row, row_criteria, curriculum_major)
                
                    project_rows.append(row)
                    row_criterias.append(row_criteria)

                    if is_no_add_limits:
                        row['receive_add_limit'] = 0

        if is_slots_combined:
            project_rows = combine_slots(project_rows)
        else:
            mark_join_ids(project_rows, int(project_id)*100)
            mark_multiline_majors(project_rows, row_criterias)

        project_rows = post_process(project_rows, post_processors)

        all_rows += project_rows
        
    for d in set(all_missing_descriptions):
        print("--> ", d.strip())

    all_rows = sort_rows(all_rows)
    
    with open(csv_filename, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)

        writer.writeheader()
        for r in all_rows:
            writer.writerow(r)

    if scoring_json_filename:
        export_json(scoring_json_filename, json_data)

if __name__ == '__main__':
    main()
