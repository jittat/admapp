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

    return render(request,
                  'criterion/index.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'admission_criterias': admission_criterias
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
                  'criterion/create.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id": m.id, "title": ("%s (%s) %s") % (m.cupt_code.title, m.cupt_code.program_type, m.cupt_code.major_title)}) for m in sorted(majors, key=(lambda m: (m.cupt_code.program_code, m.cupt_code.major_title)))]),
                   })


@user_login_required
def select_curriculum_major(request, project_id, round_id):
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

    selected_cupt_codes = set([m.cupt_code_id for m in curriculum_majors])
    for major in major_choices:
        major.is_selected = major.id in selected_cupt_codes

    return render(request,
                  'criterion/select_curriculum_majors.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'major_choices': major_choices,
                   })


    
