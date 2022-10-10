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
from .cuptexport_fields import CONDITION_FILE_FIELD_STR, SCORING_FILE_FIELD_STR

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
    for curriculum_major in get_all_curriculum_majors(project):
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


CONDITION_FILE_FIELDS = [f.strip() for f in CONDITION_FILE_FIELD_STR.split() if f.strip() != '']
SCORING_FILE_FIELDS = [f.strip() for f in SCORING_FILE_FIELD_STR.split() if f.strip() != '']

def write_csv_header(writer, fields):
    writer.writerow(fields)

def write_condition_row(writer, row):
    pass

def sort_csv_rows(rows):
    def row_key(r):
        return (r['project_id'][:2], r['program_id'], r['major_id'], r['project_id'])
    
    keyrows = [(row_key(r),r) for r in rows]
    return [r[1] for r in sorted(keyrows)]

def load_all_criterias():
    admission_criterias = {}
    curriculum_majors = { cm.id: cm
                          for cm
                          in CurriculumMajor.objects.select_related('cupt_code').all() }

    curriculum_major_admission_criterias = { cmac.admission_criteria_id: cmac
                                             for cmac in CurriculumMajorAdmissionCriteria.objects.all() }

    curriculum_major_admission_criteria_map = {}

    for id in curriculum_major_admission_criterias:
        cmac = curriculum_major_admission_criterias[id]
        cmac.curriculum_major = curriculum_majors[cmac.curriculum_major_id]
        if cmac.admission_criteria_id not in curriculum_major_admission_criteria_map:
            curriculum_major_admission_criteria_map[cmac.admission_criteria_id] = []
        curriculum_major_admission_criteria_map[cmac.admission_criteria_id].append(cmac)
    
    for criteria in (AdmissionCriteria
                     .objects
                     .filter(is_deleted=False)
                     .order_by('faculty_id')):
        if criteria.admission_project_id not in admission_criterias:
            admission_criterias[criteria.admission_project_id] = []

        admission_criterias[criteria.admission_project_id].append(criteria)

        criteria.curriculummajoradmissioncriterias = curriculum_major_admission_criteria_map[criteria.id]

    return admission_criterias

def extract_condition_rows(project, admission_criterias):
    return []

@user_login_required
def export_required_csv(request):
    user = request.user
    if not user.profile.is_admission_admin:
        return redirect(reverse('backoffice:index'))

    csv_filename = f"conditions-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{csv_filename}"'},
    )

    writer = csv.DictWriter(response, fieldnames=CONDITION_FILE_FIELDS)
    writer.writeheader()

    all_rows = []

    admission_projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True).all()
    admission_criterias = load_all_criterias()
    
    for project in admission_projects:
        rows = extract_condition_rows(project, admission_criterias[project.id])
        all_rows += rows

    rows = sort_csv_rows(all_rows)
    for r in rows:
        write_condition_row(writer, r)
    
    return response
