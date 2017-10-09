from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication

from backoffice.views.permissions import can_user_view_project

@login_required
def index(request, project_id, round_id):
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    if not can_user_view_project(request.user, project):
        return HttpResponseForbidden()

    project_applications = ProjectApplication.objects.filter(admission_project=project, 
                                                             admission_round=admission_round, 
                                                             is_canceled=False).all()
    applicants = [a.applicant for a in project_applications]

    return render(request,
                  'backoffice/showlist.html',
                  {'applicants': applicants })