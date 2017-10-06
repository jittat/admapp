from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.forms import ModelForm
from django.http import HttpResponseForbidden, HttpResponse

import json
import os

from regis.models import Applicant
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument, UploadedDocument

class UploadedDocumentForm(ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ['uploaded_file']

def upload_form_for(project_uploaded_document):
    return UploadedDocumentForm()

def upload_check(form, size_limit, allowed_extentions):
    if not form.is_valid():
        return (False, 'FORM_ERROR')

    cleaned_data = form.cleaned_data['uploaded_file']
    if size_limit <= cleaned_data.size:
        return (False, 'SIZE_ERROR')

    name, extension = os.path.splitext(cleaned_data.name)
    extension = extension[1:]
    if not extension in allowed_extentions:
        return (False, 'EXT_ERROR')

    return (True, 'OK')


@appl_login_required
def upload(request, document_id):
    applicant = request.applicant
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,
                                                  pk=document_id)
    if request.method != 'POST':
        return HttpResponseForbidden()
    size_limit = project_uploaded_document.size_limit
    allowed_extentions = project_uploaded_document.allowed_extentions.split(',')

    form = UploadedDocumentForm(request.POST, request.FILES)

    is_valid, result_code = upload_check(form, size_limit, allowed_extentions)
    if is_valid:
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
        context = {
            'project_uploaded_document': project_uploaded_document,
        }
        print(context['project_uploaded_document'])
        result = {'result': 'OK',
                            'html': template.render(context,request),
        }
    else:
        result = {'result': result_code}

    return HttpResponse(json.dumps(result),
                        content_type='application/json')
