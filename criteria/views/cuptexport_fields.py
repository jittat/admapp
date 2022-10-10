CONDITION_FILE_FIELD_STR = """
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
min_tgat
min_tgat1
min_tgat2
min_tgat3
min_tpat1
min_tpat11
min_tpat12
min_tpat13
min_tpat2
min_tpat21
min_tpat22
min_tpat23
min_tpat3
min_tpat4
min_tpat5
min_a_lv_61
min_a_lv_62
min_a_lv_63
min_a_lv_64
min_a_lv_65
min_a_lv_66
min_a_lv_70
min_a_lv_81
min_a_lv_82
min_a_lv_83
min_a_lv_84
min_a_lv_85
min_a_lv_86
min_a_lv_87
min_a_lv_88
min_a_lv_89
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
min_su005
min_su006
min_su007
min_su008
min_su009
min_su010
min_su011
min_su012
min_su013
min_su014
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

SCORING_FILE_FIELD_STR = """
type
program_id
major_id
project_id
project_name_th
cal_type
cal_subject_name
cal_score_sum
t_score
priority_score 
min_total_score
gpax
gpa21
gpa22
gpa23
gpa24
gpa25
gpa26
gpa27
gpa28
gpa29
gpa22_23
gpa22_23_28
tgat
tgat1
tgat2
tgat3
tpat1
tpat11
tpat12
tpat13
tpat2
tpat21
tpat22
tpat23
tpat3
tpat4
tpat5
a_lv_61
a_lv_62
a_lv_63
a_lv_64
a_lv_65
a_lv_66
a_lv_70
a_lv_81
a_lv_82
a_lv_83
a_lv_84
a_lv_85
a_lv_86
a_lv_87
a_lv_88
a_lv_89
vnet_51
vnet_511
vnet_512
vnet_513
vnet_514
toefl_ibt
toefl_pbt
toefl_cbt
toefl_ipt
ielts
toeic
cutep
tuget
kept
psutep
kuept
cmuetegs
swu_set
det
mu_elt
sat
cefr
ged_score
cotmes_01
cotmes_02
cotmes_03
mu001
mu002
mu003
su001
su002
su003
su004
su005
su006
su007
su008
su009
su010
su011
su012
su013
su014
tu001
tu002
tu003
tu004
tu005
tu061
tu062
tu071
tu072
tu081
tu082
tu091
tu092
netsat_math
netsat_lang
netsat_sci
netsat_phy
netsat_chem
netsat_bio
gsat
gsat_l
gsat_m
"""

CONDITION_FILE_ZERO_FIELD_STR = """
project_name_en
gender_male_number
gender_female_number
join_id
"""

SCORING_FILE_ZERO_FIELD_STR = """
"""

EXAM_FIELD_MAP = {
    'GPAX_5_SEMESTER': '',
    'GPAX': 'gpax',
    'UNIT_MATH': 'credit_gpa22',
    'UNIT_FOREIGN': 'credit_gpa28',
    'UNIT_SCI': 'credit_gpa23',
    'GPAX_MATH': 'gpa22',
    'GPAX_FOREIGN': 'gpa28',
    'GPAX_SCI': 'gpa23',
    'TGAT': 'tgat',
    'TGAT1': 'tgat1',
    'TGAT2': 'tgat2',
    'TGAT3': 'tgat3',
    'TPAT1': 'tpat1',
    'TPAT2': 'tpat2',
    'TPAT21': 'tpat21',
    'TPAT22': 'tpat22',
    'TPAT23': 'tpat23',
    'TPAT3': 'tpat3',
    'TPAT4': 'tpat4',
    'TPAT5': 'tpat5',
    'A61Math1': 'a_lv_61',
    'A62Math2': 'a_lv_62',
    'A63Sci': 'a_lv_63',
    'A64Phy': 'a_lv_64',
    'A65Chem': 'a_lv_65',
    'A66Bio': 'a_lv_66',
    'A70Soc': 'a_lv_70',
    'A81Thai': 'a_lv_81',
    'A82Eng': 'a_lv_82',
    'A83Fre': 'a_lv_83',
    'A84Ger': 'a_lv_84',
    'A85Jap': 'a_lv_85',
    'A86Kor': 'a_lv_86',
    'A87Chi': 'a_lv_87',
    'A88Bal': 'a_lv_88',
    'A89Spn': 'a_lv_89',
    'VNET': 'vnet_51',
    'TOEFL_PBT_ITP': '',
    'TOEFL_CBT': 'toefl_cbt',
    'TOEFL_IBT': 'toefl_itp',
    'IELTS': 'ielts',
    'TOEIC': 'toeic',
    'OOPT': '',
    'KU_EPT': 'kuept',
    'CU_TEP': 'cutep',
    'TU_GET': 'tuget',
    'KKU_KEPT': 'kept',
    'PSU_TEP': 'psutep',
    'CMU_ETEGS': 'cmuetegs',
    'SWU_SET': 'swu_set',
    'DET': 'det',
    'MU_ELT': '',
}
