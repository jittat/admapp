from django.shortcuts import render

from regis.models import Applicant
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument

from appl.views.upload import upload_form_for

@appl_login_required
def index(request):
    project_upload_documents = ProjectUploadedDocument.objects.filter(admission_project=None).all()

    for d in project_upload_documents:
        d.form = upload_form_for(d)
    
    return render(request,
                  'appl/index.html',
                  { 'applicant': request.applicant,
                    'project_upload_documents': project_upload_documents })

        
