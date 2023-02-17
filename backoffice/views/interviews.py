from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from appl.models import Faculty, AdmissionProject, AdmissionRound
from backoffice.decorators import user_login_required
from backoffice.views.permissions import can_user_adjust_major, can_user_confirm_major_adjustment
from regis.models import LogItem

@user_login_required
def interview_form(request, admission_round_id, faculty_id, description_id):
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)
    faculty = get_object_or_404(Faculty, pk=faculty_id)

    project_id = request.GET.get('project','0')
    if project_id != '0':
        admission_project = get_object_or_404(AdmissionProject,pk=project_id)
    else:
        admission_project = None
    
    return render(request,
                  'backoffice/interviews/description.html',
                  { 'admission_round': admission_round,
                    'admission_project': admission_project,
                    'faculty': faculty })
