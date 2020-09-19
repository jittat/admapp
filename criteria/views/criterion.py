import csv
import json
from datetime import datetime
from django.core import serializers

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major, AdmissionResult, Faculty
from appl.models import ProjectUploadedDocument, UploadedDocument, ExamScoreProvider, MajorInterviewDescription

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major, can_user_view_applicants_in_major
from backoffice.decorators import user_login_required


@user_login_required
def index(request):
    user = request.user
    # mock
    project_id = 1
    round_id = 2
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
        user_major_number = user.profile.major_number
    else:
        faculty = None
        user_major_number = user.profile.ANY_MAJOR

    majors = project.major_set.select_related(
        'faculty').order_by('faculty_id').all()

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]


    
    return render(request,
                  'criterion/index.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': majors,
                   'user_major_number': user_major_number,
                   'any_major': user.profile.ANY_MAJOR,
                   })


def create(request, project_id, round_id):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)

    if not can_user_view_project(user, project):
        return redirect(reverse('criteria:index'))

    if not user.profile.is_admission_admin:
        faculty = user.profile.faculty
        user_major_number = user.profile.major_number
    else:
        faculty = None
        user_major_number = user.profile.ANY_MAJOR

    majors = project.major_set.select_related(
        'faculty').order_by('faculty_id').all()

    if faculty:
        majors = [m for m in majors if m.faculty_id == faculty.id]

    return render(request,
                  'criterion/create.html',
                  {'project': project,
                   'admission_round': admission_round,
                   'faculty': faculty,
                   'majors': json.dumps([dict({"id":m.id, "title":m.title}) for m in majors]),

                   'user_major_number': user_major_number,
                   'any_major': user.profile.ANY_MAJOR,
                   })
