from django.shortcuts import render

from regis.models import Applicant
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument, AdmissionRound

from appl.views.upload import upload_form_for

def prepare_uploaded_document_forms(applicant, project_uploaded_documents):
    for d in project_uploaded_documents:
        d.form = upload_form_for(d)
        d.applicant_uploaded_documents = d.get_uploaded_documents_for_applicant(applicant)
        

@appl_login_required
def index(request):
    applicant = request.applicant
    
    project_uploaded_documents = ProjectUploadedDocument.get_common_documents()
    prepare_uploaded_document_forms(applicant, project_uploaded_documents)

    admission_round = AdmissionRound.get_available()
    if admission_round:
        admission_projects = admission_round.get_available_projects()
    else:
        admission_projects = []
        
    return render(request,
                  'appl/index.html',
                  { 'applicant': applicant,
                    'project_uploaded_documents': project_uploaded_documents,

                    'admission_round': admission_round,
                    'admission_projects': admission_projects })

        
