import csv
import json
from decimal import Decimal

from datetime import datetime
from django.core import serializers

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db import transaction

from django.http import Http404

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major, AdmissionResult, Faculty

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major, can_user_view_applicants_in_major
from backoffice.decorators import user_login_required

from criteria.models import CurriculumMajor, AdmissionCriteria, ScoreCriteria, CurriculumMajorAdmissionCriteria, MajorCuptCode, CuptExportConfig

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

@user_login_required
def project_validation(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    global_messages = []
    
    project_export_config = load_export_config(project)
    if 'errors' in project_export_config:
        global_messages += ['JSON error: ' + e for e in project_export_config['errors']]

    additional_projects, cupt_code_custom_projects = extract_additional_projects(project_export_config)

    if not user.profile.is_admission_admin:
        return redirect(reverse('backoffice:index'))

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
