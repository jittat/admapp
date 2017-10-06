from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse
from appl.models import UploadedDocument
from magic import Magic
import os

def document_view(request,document_id = 0):
    uploaded_document = UploadedDocument.objects.get(pk=document_id)
    doc_file = uploaded_document.uploaded_file

    doc_abs_path = os.path.join(settings.MEDIA_ROOT, doc_file.name)
    mime = Magic(mime=True).from_file(doc_abs_path)

    response = HttpResponse(doc_file)
    response['Content-Type'] = mime

    return response
