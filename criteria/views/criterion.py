import csv
import json
from decimal import Decimal

from datetime import datetime
from django.core import serializers

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db import transaction

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major, AdmissionResult, Faculty
from appl.models import ProjectUploadedDocument, UploadedDocument, ExamScoreProvider, MajorInterviewDescription

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major, can_user_view_applicants_in_major
from backoffice.decorators import user_login_required

from criteria.models import CurriculumMajor, AdmissionCriteria, ScoreCriteria, CurriculumMajorAdmissionCriteria, MajorCuptCode

def get_all_curriculum_majors(project, faculty=None):
    if not faculty:
        majors = CurriculumMajor.objects.filter(
            admission_project_id=project.id).select_related('cupt_code')
    else:
        majors = CurriculumMajor.objects.filter(
            admission_project_id=project.id,
            faculty_id=faculty.id).select_related('cupt_code')

    return majors

@user_login_required
def project_index(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
        admission_criterias = AdmissionCriteria.objects.filter(
            admission_project_id=project_id, faculty_id=faculty.id)
    else:
        faculty = None
        admission_criterias = AdmissionCriteria.objects.filter(
            admission_project_id=project_id)

        
    curriculum_majors = get_all_curriculum_majors(project, faculty)
    curriculum_majors_with_criterias = []
    for criteria in admission_criterias:
        curriculum_majors_with_criterias += criteria.curriculummajor_set.all()
    curriculum_majors_with_criteria_ids = set([m.id for m
                                               in curriculum_majors_with_criterias])

    free_curriculum_majors = [m for m in curriculum_majors
                              if m.id not in curriculum_majors_with_criteria_ids]

    return render(request,
                  'criterion/index.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'admission_criterias': admission_criterias,
                   'free_curriculum_majors': free_curriculum_majors,
                   })


@user_login_required
def create(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None

    majors = get_all_curriculum_majors(project, faculty)

    if request.method == 'POST':
        score_criteria_dict = dict()
        for key in request.POST:
            splitted_keys = key.split('_')
            if splitted_keys[0] == "required" or splitted_keys[0] == "scoring":
                data_key = splitted_keys[0]+'_'+splitted_keys[1]
                if data_key not in score_criteria_dict:
                    order_numbers = splitted_keys[1].split('.')
                    initial_data = {
                        "criteria_type": splitted_keys[0],
                        "primary_order": int(order_numbers[0]),
                        "secondary_order": 0
                    }
                    if len(order_numbers) == 2:
                        initial_data["secondary_order"] = int(order_numbers[1])

                    score_criteria_dict[data_key] = initial_data

                value = request.POST[key]
                if value.isnumeric():
                    value = Decimal(value)

                score_criteria_dict[data_key][splitted_keys[2]
                                              ] = value
        with transaction.atomic():
            admission_criteria = AdmissionCriteria(
                admission_project=project, version=1, faculty=faculty)

            admission_criteria.save()

            for key in score_criteria_dict:
                s = score_criteria_dict[key]
                scoring_criteria = ScoreCriteria(
                    admission_criteria=admission_criteria,
                    version=1,
                    primary_order=s["primary_order"],
                    secondary_order=s["secondary_order"],
                    criteria_type=s["criteria_type"],
                    score_type="OTHER",
                    value=s["value"],
                    unit=(s["unit"] if "unit" in s else ""),
                    description=s["title"])
                scoring_criteria.save()

            major_criteria = CurriculumMajorAdmissionCriteria(
                admission_criteria=admission_criteria,
                curriculum_major=majors[0],
                slots=1000
            )

            major_criteria.save()

        return render(request, 'criterion/complete.html', {'project': project, 'admission_round': admission_round})

    return render(request,
                  'criterion/create.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in sorted(majors, key=(lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   })


# TODO: get real data
@user_login_required
def edit(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None

    majors = CurriculumMajor.objects.filter(
        admission_project_id=project_id).select_related('cupt_code')

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]

    if request.method == 'POST':
        score_criteria_dict = dict()
        for key in request.POST:
            splitted_keys = key.split('_')
            if splitted_keys[0] == "required" or splitted_keys[0] == "scoring":
                data_key = splitted_keys[0]+'_'+splitted_keys[1]
                if data_key not in score_criteria_dict:
                    order_numbers = splitted_keys[1].split('.')
                    initial_data = {
                        "criteria_type": splitted_keys[0],
                        "primary_order": int(order_numbers[0]),
                        "secondary_order": 0
                    }
                    if len(order_numbers) == 2:
                        initial_data["secondary_order"] = int(order_numbers[1])

                    score_criteria_dict[data_key] = initial_data

                value = request.POST[key]
                if value.isnumeric():
                    value = Decimal(value)

                score_criteria_dict[data_key][splitted_keys[2]
                                              ] = value
        with transaction.atomic():
            admission_criteria = AdmissionCriteria(
                admission_project=project, version=1, faculty=faculty)

            admission_criteria.save()

            for key in score_criteria_dict:
                s = score_criteria_dict[key]
                scoring_criteria = ScoreCriteria(
                    admission_criteria=admission_criteria,
                    version=1,
                    primary_order=s["primary_order"],
                    secondary_order=s["secondary_order"],
                    criteria_type=s["criteria_type"],
                    score_type="OTHER",
                    value=s["value"],
                    unit=(s["unit"] if "unit" in s else ""),
                    description=s["title"])
                scoring_criteria.save()

            major_criteria = CurriculumMajorAdmissionCriteria(
                admission_criteria=admission_criteria,
                curriculum_major=majors[0],
                slots=1000
            )

            major_criteria.save()

        return render(request, 'criterion/complete.html', {'project': project, 'admission_round': admission_round})

    return render(request,
                  'criterion/edit.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in sorted(majors, key=(lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   })


@user_login_required
def select_curriculum_major(request, project_id, round_id, code_id=0, value='none'):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
    else:
        faculty = None

    major_choices = MajorCuptCode.objects.filter(faculty=faculty)

    curriculum_majors = CurriculumMajor.objects.filter(admission_project_id=project_id,
                                                       faculty=faculty).all()

    selected_curriculum_majors = dict([(m.cupt_code_id, m) for m in curriculum_majors])
    for major in major_choices:
        major.is_selected = major.id in selected_curriculum_majors
        if major.is_selected:
            major.can_be_deleted = not selected_curriculum_majors[major.id].is_with_some_admission_criteria()
        
    if request.method == 'POST':
        major_cupt_codes = [m for m in major_choices if m.id == int(code_id)]
        if len(major_cupt_codes)!=1:
            return HttpResponseNotFound()
        major_cupt_code = major_cupt_codes[0]

        if value == 'select':
            curriculum_major = CurriculumMajor(admission_project=project,
                                               cupt_code=major_cupt_code,
                                               faculty=faculty)
            curriculum_major.save()
            return HttpResponse('true')
        elif value == 'unselect':
            if not major_cupt_code.is_selected or (not major_cupt_code.can_be_deleted):
                return HttpResponseForbidden()
            curriculum_major = selected_curriculum_majors[major_cupt_code.id]
            curriculum_major.delete()
            return HttpResponse('false')
        return HttpResponseNotFound()
            
    return render(request,
                  'criterion/select_curriculum_majors.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'major_choices': major_choices,
                   })


    
