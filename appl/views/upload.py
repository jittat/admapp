from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.forms import ModelForm
from django.http import HttpResponseForbidden

from regis.models import Applicant
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument, UploadedDocument

class UploadedDocumentForm(ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ['uploaded_file']

def upload_form_for(project_uploaded_document):
    return UploadedDocumentForm()

@appl_login_required
def upload(request, document_id):
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,
                                                  pk=document_id)
    if request.method != 'POST':
        return HttpResponseForbidden()

    form = UploadedDocumentForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_document = form.save(commit=False)
        uploaded_document.applicant = request.applicant
        uploaded_document.project_uploaded_document = project_uploaded_document
        uploaded_document.admission_project = project_uploaded_document.admission_project
        uploaded_document.rank = 0
        uploaded_document.orginal_filename = uploaded_document.uploaded_file.name
        uploaded_document.save()

    return redirect(reverse('appl:index'))
