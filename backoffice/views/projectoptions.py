from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponse
from django.core import serializers
import json

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, ProjectApplication, EducationalProfile, PersonalProfile, Payment

from backoffice.models import Profile

from backoffice.decorators import user_login_required, super_admin_login_required
from .permissions import can_user_view_project

@user_login_required
def show_project_application_info(request):
    user = request.user

    if not user.is_super_admin:
        redirect(reverse('backoffice:index'))

    admission_projects = AdmissionProject.objects.filter(is_available=True).all()

    return render(request,
                  'backoffice/project_application_info.html',
                  { 'admission_projects': admission_projects,
                  })


@user_login_required
def show_project_options(request):
    user = request.user
    if not user.is_super_admin:
        redirect(reverse('backoffice:index'))

    admission_projects = AdmissionProject.objects.filter(is_visible_in_backoffice=True).all()

    return render(request,
                  'backoffice/project_options.html',
                  { 'admission_projects': admission_projects,
                    'student_type_choices': AdmissionProject.STUDENT_TYPE_CHOICES,
                    'school_type_choices': AdmissionProject.SCHOOL_TYPE_CHOICES,
                  })

@user_login_required
def update_project_options(request, project_id, update_type, val):
    user = request.user
    if not user.is_super_admin:
        redirect(reverse('backoffice:index'))

    admission_project = get_object_or_404(AdmissionProject, pk=project_id)

    data = {
        'result': 'OK',
        'message': '',
    }

    try:
        if update_type == 'student':
            admission_project.admission_student_type = int(val)
            msg = admission_project.get_admission_student_type_display()
            admission_project.save()
        else:
            admission_project.admission_school_type = int(val)
            msg = admission_project.get_admission_school_type_display()
            admission_project.save()
        data['message'] = msg
        
    except:
        data = {
            'result': 'ERROR',
            'message': ''
        }

    return HttpResponse(json.dumps(data),
                        content_type='application/json')
