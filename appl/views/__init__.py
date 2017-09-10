from django.shortcuts import render

from regis.models import Applicant
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument

from appl.views.upload import upload_form_for

@appl_login_required
def index(request):
    applicant = request.applicant
    project_uploaded_documents = ProjectUploadedDocument.objects.filter(admission_project=None).all()

    for d in project_uploaded_documents:
        d.form = upload_form_for(d)
        d.applicant_uploaded_documents = d.uploaded_document_for_applicant(applicant)
    
    return render(request,
                  'appl/index.html',
                  { 'applicant': applicant,
                    'project_uploaded_documents': project_uploaded_documents })

        
