from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.forms import ModelForm
from django.http import HttpResponseForbidden, HttpResponse

import json

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
    applicant = request.applicant
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,
                                                  pk=document_id)
    if request.method != 'POST':
        return HttpResponseForbidden()
    size_limit = project_uploaded_document.size_limit
    form = UploadedDocumentForm(request.POST, request.FILES)
    if form.is_valid():
        print(size_limit, form.cleaned_data['uploaded_file'].size)
        if not project_uploaded_document.can_have_multiple_files:
            old_uploaded_documents = project_uploaded_document.get_uploaded_documents_for_applicant(applicant)
            for odoc in old_uploaded_documents:
                odoc.uploaded_file.delete()
                odoc.delete()

        uploaded_document = form.save(commit=False)
        uploaded_document.applicant = request.applicant
        uploaded_document.project_uploaded_document = project_uploaded_document
        uploaded_document.admission_project = project_uploaded_document.admission_project
        uploaded_document.rank = 0
        uploaded_document.orginal_filename = uploaded_document.uploaded_file.name
        uploaded_document.save()

        from django.template import loader

        template = loader.get_template('appl/include/document_upload_form.html')

        project_uploaded_document.form = upload_form_for(project_uploaded_document)
        project_uploaded_document.applicant_uploaded_documents = project_uploaded_document.get_uploaded_documents_for_applicant(applicant)

        result = {'result': 'OK',
                  'html': template.render({ 'project_uploaded_document': project_uploaded_document },
                                          request) }
    else:
        result = {'result': 'ERROR'}
    return HttpResponse(json.dumps(result),
                        content_type='application/json')
