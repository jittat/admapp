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

    project_applications = ProjectApplication.find_for_project_and_round(project,
                                                                         admission_round,
                                                                         True)
    major_map = dict([(m.number,m) for m in project.major_set.all()])
    applicants = []

    for app in project_applications:
        applicant = app.applicant

        try:
            major_selection = app.major_selection
            applicant.major_selection = major_selection
            applicant.majors = []
            for num in major_selection.get_major_numbers():
                applicant.majors.append(major_map[num])
            if project.max_num_selections == 1:
                if len(applicant.majors)!=0:
                    applicant.major_number = applicant.majors[0].number
                else:
                    applicant.major_number = 1000000000
        except:
            applicant.major_selection = None
            applicant.majors = []
            applicant.major_number = 1000000000
        
        applicants.append(applicant)

    if project.max_num_selections==1:
        amap = dict([(a.id,a) for a in applicants])
        sorted_applicants = [x[1] for x in sorted([(applicant.major_number,
                                                    applicant.id) for applicant
                                                   in applicants])]
        applicants = [amap[i] for i in sorted_applicants]

        sorted_by_majors = True
    else:
        sorted_by_majors = False
        
    return render(request,
                  'backoffice/show_project_in_round.html',
                  { 'project': project,
                    'admission_round': admission_round,
                    'applicants': applicants,
                    'sorted_by_majors': sorted_by_majors })
