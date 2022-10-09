import csv
import json
from decimal import Decimal

from datetime import datetime
from django.core import serializers

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db import transaction
from django.db.models import Q

from django.http import Http404

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major, AdmissionResult, Faculty

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major, can_user_view_applicants_in_major
from backoffice.decorators import user_login_required

from criteria.models import CurriculumMajor, AdmissionCriteria, ScoreCriteria, CurriculumMajorAdmissionCriteria, MajorCuptCode, CuptExportConfig

from criteria.criteria_options import REQUIRED_SCORE_TYPE_TAGS, SCORING_SCORE_TYPE_TAGS

from . import prepare_admission_criteria, get_all_curriculum_majors

def combine_slots(curriculum_major_rows):
    if len(curriculum_major_rows) == 0:
        return []
    
    new_rows = []

    rr = curriculum_major_rows[0]
    rr['add_limit'] = '0'
    for r in curriculum_major_rows[1:]:
        rr['slots'] += r['slots']
        rr['validation_messages'] += r['validation_messages']

    return [rr]


def is_criteria_match(row, custom_project):
    for key, str_key in [('score-include', 'scoring_criteria_str'),
                         ('require-include', 'required_criteria_str')]:
        if key in custom_project:
            if custom_project[key] not in row[str_key]:
                return False
    return True


def validate_project_ids(curriculum_major_rows, additional_projects, cupt_code_custom_projects):
    if len(curriculum_major_rows) > 1:
        program_id = curriculum_major_rows[0]['curriculum_major'].cupt_code.get_program_major_code_as_str()

        if program_id in cupt_code_custom_projects:
            custom_projects = cupt_code_custom_projects[program_id]
        else:
            custom_projects = []

        for r in curriculum_major_rows:
            r['required_criteria_str'] = r['criteria'].get_all_required_score_criteria_as_str()
            r['scoring_criteria_str'] = r['criteria'].get_all_scoring_score_criteria_as_str()

        if len(custom_projects) == 0:
            for r in curriculum_major_rows:
                r['validation_messages'].append(f'Too many rows - {len(custom_projects)} in config')
                r['validation_messages'].append(r['required_criteria_str'])
                r['validation_messages'].append(r['scoring_criteria_str'])
            return

        for r in curriculum_major_rows:
            custom_project = next((p for p in custom_projects if is_criteria_match(r, p)), None)
            #print(r,[p for p in custom_projects if is_criteria_match(r, p)])
            #print("---------")
            if custom_project:
                r['project_id'] = custom_project['project_id']
                if r['project_id'] in additional_projects:
                    r['validation_messages'].append(f"changed to {r['project_id']} ({additional_projects[r['project_id']]})")
                    r['validation_messages'].append(r['required_criteria_str'])
                    r['validation_messages'].append(r['scoring_criteria_str'])
                else:
                    r['validation_messages'].append(f"changed to {r['project_id']} (PROJECT NOT FOUND)")
                    r['validation_messages'].append(r['required_criteria_str'])
                    r['validation_messages'].append(r['scoring_criteria_str'])

        project_id_sets = set([r['project_id'] for r in curriculum_major_rows])
        if len(project_id_sets) != len(curriculum_major_rows):
            for r in curriculum_major_rows:
                r['validation_messages'].append('Too many rows')

def load_export_config(project):
    configs = CuptExportConfig.objects.filter(admission_project=project)

    config = {}
    for c in configs:
        this_config = {}

        if c.config_json.strip() == '':
            continue
        
        import json
        try:
            this_config = json.loads(c.config_json)
        except json.JSONDecodeError as err: 
            this_config['errors'] = [err.msg]

        for k in this_config:
            if k in config:
                config[k] += this_config[k]
            else:
                config[k] = this_config[k]
    return config

def extract_additional_projects(config):
    additional_projects = {}
    cupt_code_custom_projects = {}
    if 'projects' in config:
        additional_projects = {p[0]: p[1] for p in config['projects']}
    if 'custom_projects' in config:
        cupt_code_custom_projects = config['custom_projects']
    return additional_projects, cupt_code_custom_projects

score_type_reverse_map = { item['description'].replace(' ',''): item['score_type'] for item in
                           REQUIRED_SCORE_TYPE_TAGS + SCORING_SCORE_TYPE_TAGS }

def normalize_score_type(description):
    description = description.replace(' ','')
    if description in score_type_reverse_map:
        return score_type_reverse_map[description]
    else:
        return 'OTHER'

def check_other_score_type(score_criterias):
    messages = []
    for c in score_criterias:
        if c.has_children():
            if c.relation:
                messages.append("Group: " + c.relation)
            else:
                messages.append("Group: ERROR")
            for ch in c.cached_children:
                if ch.score_type == 'OTHER':
                    ch.score_type = normalize_score_type(ch.description)
                    if ch.score_type == 'OTHER':
                        messages.append("child: " + ch.score_type + ": " + ch.description)
        else:
            if c.score_type == 'OTHER':
                c.score_type = normalize_score_type(c.description)
                if c.score_type == 'OTHER':
                    messages.append(c.score_type + ": " + c.description)

    return score_criterias, messages
    
    
NONE_WARNING_IGNORE_SCORE_TYPES = set(['GPAX'])

def extract_one_required_score_criteria(score_criteria):
    if (score_criteria.value != None) and (score_criteria.value != 0):
        item = {
            'score_type': score_criteria.score_type,
            'min_value': float(score_criteria.value),
        }
        return item, None
    elif score_criteria.value == None:
        if score_criteria.score_type not in NONE_WARNING_IGNORE_SCORE_TYPES:
            return None, 'Value=None: '+ score_criteria.description
        else:
            return None, None
    else:
        return None, None

def extract_or_group_required_criteria(score_criteria):
    items = []
    message = None
    children = score_criteria.cached_children
    for c in children:
        item, msg = extract_one_required_score_criteria(c)
        if item != None:
            items.append(item)
        if msg != None:
            message = 'ERROR: bad group item'
    if message == None:
        return { 'grouping': 'OR',
                 'score_type': 'GROUP-OR',
                 'children': items }, message
    else:
        return None, message
        
def extract_required_criteria(admission_criteria):
    or_count = 0
    messages = []

    score_criterias = admission_criteria.get_all_required_score_criteria()
    score_criterias, other_score_type_messages = check_other_score_type(score_criterias)
    messages += other_score_type_messages

    required_scores = []
    for c in score_criterias:
        if not c.has_children():
            item, msg = extract_one_required_score_criteria(c)
            if item != None:
                required_scores.append(item)
            if msg != None:
                messages.append(msg)
        else:
            if c.relation == 'OR':
                or_count += 1
                if or_count > 1:
                    messages.append('ERROR: Too many ORs')

                item, msg = extract_or_group_required_criteria(c)
                if item != None:
                    required_scores.append(item)
                if msg != None:
                    messages.append(msg)
            else:
                messages.append('ERROR: other relation ' + c.relation)
            
    return required_scores, messages

def extract_one_scoring_score_criteria(score_criteria):
    if (score_criteria.value != None) and (score_criteria.value != 0):
        item = {
            'score_type': score_criteria.score_type,
            'base_weight': float(score_criteria.value),
        }
        return item, None
    elif score_criteria.value == None:
        if score_criteria.score_type not in NONE_WARNING_IGNORE_SCORE_TYPES:
            return None, 'Value=None: '+ score_criteria.description
        else:
            return None, None
    else:
        return None, None

def extract_max_group_scoring_criteria(score_criteria):
    items = []
    children = score_criteria.cached_children
    for c in children:
        items.append({'score_type': c.score_type,
                      'value': c.value })
    return { 'grouping': 'MAX',
             'score_type': 'GROUP-MAX',
             'children': items,
             'base_weight': float(score_criteria.value) }, None
        
def extract_scoring_criteria(admission_criteria):
    messages = []
    max_count = 0
    
    score_criterias = admission_criteria.get_all_scoring_score_criteria()
    score_criterias, other_score_type_messages = check_other_score_type(score_criterias)
    messages += other_score_type_messages
                
    scoring_scores = []
    for c in score_criterias:
        if not c.has_children():
            item, msg = extract_one_scoring_score_criteria(c)
            if item != None:
                scoring_scores.append(item)
            if msg != None:
                messages.append(msg)
        else:
            if c.relation == 'MAX':
                max_count += 1
                if max_count > 1:
                    messages.append('ERROR: Too many MAXs')

                item, msg = extract_max_group_scoring_criteria(c)
                if item != None:
                    scoring_scores.append(item)
                if msg != None:
                    messages.append(msg)
            else:
                messages.append('ERROR: other relation ' + c.relation)
            
    return scoring_scores, messages

@user_login_required
def project_validation(request, project_id, round_id):
    user = request.user
    if not user.profile.is_admission_admin:
        return redirect(reverse('backoffice:index'))

    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    global_messages = []
    
    project_export_config = load_export_config(project)
    if 'errors' in project_export_config:
        global_messages += ['JSON error: ' + e for e in project_export_config['errors']]

    additional_projects, cupt_code_custom_projects = extract_additional_projects(project_export_config)

    faculties = Faculty.objects.all()
    
    admission_criterias = (AdmissionCriteria
                           .objects
                           .filter(admission_project_id=project_id,
                                   is_deleted=False)
                           .order_by('faculty_id'))
    
    curriculum_majors = get_all_curriculum_majors(project)

    majors = {}
    
    for admission_criteria in admission_criterias:
        curriculum_major_admission_criterias = admission_criteria.curriculummajoradmissioncriteria_set.select_related('curriculum_major').all()
        
        if not project.is_cupt_export_only_major_list:
            admission_criteria.cache_score_criteria_children()
            admission_criteria.extracted_required_criteria = extract_required_criteria(admission_criteria)
            admission_criteria.extracted_scoring_criteria = extract_scoring_criteria(admission_criteria)

        for mc in curriculum_major_admission_criterias:
            curriculum_major = mc.curriculum_major

            row_criteria = admission_criteria

            if project.is_cupt_export_only_major_list:
                row_criteria = None

            if curriculum_major.id not in majors:
                majors[curriculum_major.id] = []

            majors[curriculum_major.id].append({
                'project_id': project.cupt_code,
                'add_limit': mc.add_limit_display(),
                
                'curriculum_major': curriculum_major,
                'slots': mc.slots,
                'criteria': row_criteria,
                'cm_ar': mc,
                'validation_messages': [],
            })
    
    if project.is_cupt_export_only_major_list:
        for mid in majors:
            majors[mid] = combine_slots(majors[mid])
    else:
        for mid in majors:
            validate_project_ids(majors[mid], additional_projects, cupt_code_custom_projects)

    free_curriculum_majors = []
    for curriculum_major in curriculum_majors:
        if curriculum_major.id not in majors:
            free_curriculum_majors.append(curriculum_major)
    
    return render(request,
                  'criteria/cuptexport/validate.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'majors': majors,
                   'free_curriculum_majors': free_curriculum_majors,
                   'validation_messages': global_messages,
                   })


@user_login_required
def index(request):
    user = request.user
    if not user.profile.is_admission_admin:
        return redirect(reverse('backoffice:index'))

    admission_projects = AdmissionProject.objects.filter(Q(is_available=True) | Q(is_visible_in_backoffice=True)).all()
    
    return render(request,
                  'criteria/cuptexport/index.html',
                  {'admission_projects': admission_projects
                   })
                  

CONDITION_FILE_FIELDS = """program_id
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

SCORING_FILE_FIELDS = """type
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

