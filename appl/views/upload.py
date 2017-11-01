import os
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.forms import ModelForm
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction

from regis.models import Applicant
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument, UploadedDocument, AdmissionRound

class UploadedDocumentForm(ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ['uploaded_file','document_url','detail']

def upload_form_for(project_uploaded_document):
    return UploadedDocumentForm()

def upload_check(form, size_limit, allowed_extentions, is_detail_required):
    if not form.is_valid():
        return (False, 'FORM_ERROR')

    cleaned_data = form.cleaned_data['uploaded_file']
    if not cleaned_data:
        return (False, 'FORM_ERROR')
    
    if size_limit <= cleaned_data.size:
        return (False, 'SIZE_ERROR')

    name, extension = os.path.splitext(cleaned_data.name)
    extension = extension[1:]
    if not extension.upper() in allowed_extentions:
        return (False, 'EXT_ERROR')

    if is_detail_required:
        if len(form.cleaned_data['detail']) == 0:
            return (False, 'DETAIL_REQUIRE')

    return (True, 'OK')


def url_check(form, is_detail_required):
    if not form.is_valid():
        return (False, 'URL_INVALID')

    if form.cleaned_data['document_url'] == '':
        return (False, 'URL_INVALID')

    if is_detail_required:
        if len(form.cleaned_data['detail']) == 0:
            return (False, 'DETAIL_REQUIRE')

    return (True, 'OK')


@appl_login_required
def upload(request, document_id):
    applicant = request.applicant
    admission_round = AdmissionRound.get_available()

    active_application = applicant.get_active_application(admission_round)
    admission_project = active_application.admission_project
    project_round = admission_project.get_project_round_for(admission_round)
    is_deadline_passed = project_round.is_deadline_passed()
    
    if is_deadline_passed:
        return HttpResponseForbidden()
            
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,
                                                  pk=document_id)
    if request.method != 'POST':
        return HttpResponseForbidden()

    form = UploadedDocumentForm(request.POST, request.FILES)

    is_detail_required = project_uploaded_document.is_detail_required
    
    if project_uploaded_document.is_url_document:
        is_valid, result_code = url_check(form, is_detail_required)
    else:
        size_limit = project_uploaded_document.size_limit
        allowed_extentions = [ext.upper() for ext in
                              project_uploaded_document.allowed_extentions.split(',')]

        is_valid, result_code = upload_check(form, size_limit, allowed_extentions, is_detail_required)

    if is_valid:
        if not project_uploaded_document.can_have_multiple_files:
            old_uploaded_documents = project_uploaded_document.get_uploaded_documents_for_applicant(applicant)
            for odoc in old_uploaded_documents:
                odoc.uploaded_file.delete()
                odoc.delete()

        uploaded_document = form.save(commit=False)
        uploaded_document.applicant = request.applicant
        uploaded_document.project_uploaded_document = project_uploaded_document
        uploaded_document.rank = 0

        if not project_uploaded_document.is_url_document:
            uploaded_document.orginal_filename = uploaded_document.uploaded_file.name
            
        uploaded_document.save()

        from django.template import loader

        template = loader.get_template('appl/include/document_upload_form.html')

        project_uploaded_document.form = upload_form_for(project_uploaded_document)
        project_uploaded_document.applicant_uploaded_documents = project_uploaded_document.get_uploaded_documents_for_applicant(applicant)
        context = {
            'applicant': applicant,
            'project_uploaded_document': project_uploaded_document,
            'toggle': 'show'
        }
        result = {'result': 'OK',
                            'html': template.render(context, request),
        }
    else:
        result = {'result': result_code}

    return HttpResponse(json.dumps(result),
                        content_type='application/json')


def get_uploaded_document_or_403(request, applicant_id, project_uploaded_document_id, document_id):

    applicant = get_object_or_404(Applicant, pk=applicant_id)
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,pk=project_uploaded_document_id)
    uploaded_document = get_object_or_404(UploadedDocument,pk=document_id)

    if uploaded_document.applicant != applicant \
    or uploaded_document.project_uploaded_document != project_uploaded_document \
    or uploaded_document.applicant != request.applicant:
        raise PermissionDenied()

    return uploaded_document


def get_file_mime_type(document):
    try:
        from magic import Magic

        doc_abs_path = os.path.join(settings.MEDIA_ROOT, document.name)
        mime_type = Magic(mime=True).from_file(doc_abs_path)
        return mime_type
    except:
        return 'image/png'


def download_uploaded_document_response(uploaded_document):
    doc_file = uploaded_document.uploaded_file

    mime = get_file_mime_type(doc_file)

    response = HttpResponse(doc_file)
    response['Content-Type'] = mime

    return response


@appl_login_required
def document_download(request, applicant_id=0, project_uploaded_document_id=0, document_id=0):

    uploaded_document = get_uploaded_document_or_403(request, applicant_id, project_uploaded_document_id, document_id)

    if int(applicant_id) != request.applicant.id:
        return HttpResponseForbidden()

    return download_uploaded_document_response(uploaded_document)


@appl_login_required
def document_delete(request, applicant_id=0, project_uploaded_document_id=0, document_id=0):
    if request.method != 'POST':
        return HttpResponseForbidden()

    try:
        with transaction.atomic():
            uploaded_document = get_uploaded_document_or_403(request, applicant_id, project_uploaded_document_id, document_id)

            applicant = get_object_or_404(Applicant, pk=applicant_id)
            admission_round = AdmissionRound.get_available()
            
            active_application = applicant.get_active_application(admission_round)
            admission_project = active_application.admission_project
            project_round = admission_project.get_project_round_for(admission_round)
            is_deadline_passed = project_round.is_deadline_passed()

            if is_deadline_passed:
                return HttpResponseForbidden()
            
            uploaded_document.delete()

            from django.template import loader
            template = loader.get_template('appl/include/document_upload_form.html')
            project_uploaded_document = get_object_or_404(ProjectUploadedDocument,pk=project_uploaded_document_id)
            project_uploaded_document.form = upload_form_for(project_uploaded_document)
            project_uploaded_document.applicant_uploaded_documents = project_uploaded_document.get_uploaded_documents_for_applicant(applicant_id)

            context = {
                'applicant': request.applicant,
                'project_uploaded_document': project_uploaded_document,
                'toggle': 'show'
                }
            result = {
                'result': 'OK',
                'html': template.render(context,request),
                }
    except:
        result = {'result': 'ERROR'}

    return HttpResponse(json.dumps(result),
                        content_type='application/json')
