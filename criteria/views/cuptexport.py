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

from criteria.models import CurriculumMajor, AdmissionCriteria, ScoreCriteria, CurriculumMajorAdmissionCriteria, MajorCuptCode

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


def validate_project_ids(curriculum_major_rows, project_export_options):
    if len(curriculum_major_rows) > 1:
        for r in curriculum_major_rows:
            r['validation_messages'].append('Too many rows')
            

@user_login_required
def project_validation(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    project_export_options = {}
    
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
            validate_project_ids(majors[mid], project_export_options)

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
                   })
