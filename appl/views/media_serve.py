from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from appl.models import UploadedDocument,Applicant,ProjectUploadedDocument
from django.core.exceptions import ObjectDoesNotExist
import os

def document_view(request,document_id=0, applicant_id=0, admission_project_id=0):
    try:
        applicant = Applicant.objects.get(pk=applicant_id)
        project_uploaded_document = ProjectUploadedDocument.objects.get(pk=admission_project_id)
        uploaded_document = UploadedDocument.objects.get(pk=document_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

    if uploaded_document.applicant != applicant or uploaded_document.project_uploaded_document != project_uploaded_document:
        return HttpResponseForbidden()

    doc_file = uploaded_document.uploaded_file

    from magic import Magic

    doc_abs_path = os.path.join(settings.MEDIA_ROOT, doc_file.name)
    mime = Magic(mime=True).from_file(doc_abs_path)

    response = HttpResponse(doc_file)
    response['Content-Type'] = mime

    return response
