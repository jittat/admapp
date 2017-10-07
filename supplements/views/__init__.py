from django.shortcuts import render, get_object_or_404

from regis.decorators import appl_login_required
from appl.models import AdmissionProject
from supplements.models import ProjectSupplement, ProjectSupplementConfig

from supplements.models import PROJECT_SUPPLEMENTS

@appl_login_required
def index(request, project_id):
    applicant = request.applicant
    admission_project = get_object_or_404(AdmissionProject,
                                          pk=project_id)
    
    supplement_configs = PROJECT_SUPPLEMENTS[admission_project.title]

    return render(request,
                  'supplements/index.html',
                  { 'applicant': applicant,
                    'admission_project': admission_project,
                    'configs': supplement_configs })
