from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from appl.models import UploadedDocument,Applicant,ProjectUploadedDocument
from django.core.exceptions import ObjectDoesNotExist
from regis.decorators import appl_login_required
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

import os

def get_uploaded_documents_or_403(request, document_id, applicant_id, admission_project_id):

    applicant = get_object_or_404(Applicant, pk=applicant_id)
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,pk=admission_project_id)
    uploaded_document = get_object_or_404(UploadedDocument,pk=document_id)

    if uploaded_document.applicant != applicant \
    or uploaded_document.project_uploaded_document != project_uploaded_document \
    or uploaded_document.applicant != request.applicant:
        raise PermissionDenied

    return uploaded_document

@appl_login_required
def document_view(request,document_id=0, applicant_id=0, admission_project_id=0):

    uploaded_document = get_uploaded_documents_or_403(request, document_id, applicant_id, admission_project_id)

    doc_file = uploaded_document.uploaded_file

    from magic import Magic

    doc_abs_path = os.path.join(settings.MEDIA_ROOT, doc_file.name)
    mime = Magic(mime=True).from_file(doc_abs_path)

    response = HttpResponse(doc_file)
    response['Content-Type'] = mime

    return response
