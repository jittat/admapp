import json
import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.utils import OperationalError
from django.forms import ModelForm
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.template.loader import select_template

from appl.document_validators import run_document_validator
from appl.models import ProjectUploadedDocument, UploadedDocument, AdmissionRound
from regis.decorators import appl_login_required
from regis.models import Applicant, LogItem


class UploadedDocumentForm(ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ['uploaded_file','document_url','detail']

def upload_form_for(project_uploaded_document):
    return UploadedDocumentForm()

def prepare_deadline_flags(project_uploaded_document, admission_project):
    """Attributes read by document_upload_form.html: whether the slot stays
    open after the application deadline, and the late-upload cut-off shown to
    the applicant."""
    doc = project_uploaded_document
    doc.uploadable_after_deadline = doc.is_uploadable_after_deadline(admission_project)
    if doc.is_late_upload_open(admission_project):
        doc.late_upload_until = admission_project.late_upload_date
    else:
        doc.late_upload_until = None

def custom_validation_check(project_uploaded_document, uploaded_file=None, document_url=None):
    """Runs the slot's custom validator (if any) after the basic checks.

    Returns (is_valid, result_code, validation_result); validation_result is
    None when no validator ran.
    """
    if project_uploaded_document is None or not project_uploaded_document.validator:
        return (True, 'OK', None)

    validation_result = run_document_validator(project_uploaded_document,
                                               uploaded_file=uploaded_file,
                                               document_url=document_url)
    if validation_result.is_valid:
        return (True, 'OK', validation_result)
    return (False, 'VALIDATION_ERROR', validation_result)


def render_validation_message(project_uploaded_document, validation_result, request):
    template = select_template([
        'appl/include/document_validation_errors/%s.html' % project_uploaded_document.validator,
        'appl/include/document_validation_errors/default.html',
    ])
    context = {
        'code': validation_result.code,
        'context': validation_result.context,
        'project_uploaded_document': project_uploaded_document,
    }
    return template.render(context, request)


def upload_check(form, size_limit, allowed_extentions, is_detail_required,
                 project_uploaded_document=None):
    if not form.is_valid():
        return (False, 'FORM_ERROR', None)

    cleaned_data = form.cleaned_data['uploaded_file']
    if not cleaned_data:
        return (False, 'FORM_ERROR', None)

    if size_limit <= cleaned_data.size:
        return (False, 'SIZE_ERROR', None)

    name, extension = os.path.splitext(cleaned_data.name)
    extension = extension[1:]
    if not extension.upper() in allowed_extentions:
        return (False, 'EXT_ERROR', None)

    if is_detail_required:
        if len(form.cleaned_data['detail']) == 0:
            return (False, 'DETAIL_REQUIRE', None)

    return custom_validation_check(project_uploaded_document, uploaded_file=cleaned_data)


def url_check(form, is_detail_required, project_uploaded_document=None):
    if not form.is_valid():
        return (False, 'URL_INVALID', None)

    if form.cleaned_data['document_url'] == '':
        return (False, 'URL_INVALID', None)

    if is_detail_required:
        if len(form.cleaned_data['detail']) == 0:
            return (False, 'DETAIL_REQUIRE', None)

    return custom_validation_check(project_uploaded_document,
                                   document_url=form.cleaned_data['document_url'])


def get_upload_kind(request, project_uploaded_document):
    """Which kind of submission this is: 'file', 'url', or None when the
    applicant submitted neither (only possible for 'any' documents)."""

    if project_uploaded_document.is_url_document:
        return 'url'
    if project_uploaded_document.is_file_document:
        return 'file'

    if request.FILES.get('uploaded_file', None):
        return 'file'
    if request.POST.get('document_url', '').strip() != '':
        return 'url'
    return None


@appl_login_required
def upload(request, document_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    applicant = request.applicant
    admission_round = AdmissionRound.get_available()

    active_application = applicant.get_active_application(admission_round)
    if active_application == None:
        try:
            active_application = applicant.accepted_application 
        except:
            active_application = None
        if active_application:
            admission_round = active_application.admission_round

    if active_application == None:
        LogItem.create('active application missing', applicant, request)
        return HttpResponse(json.dumps({'result': 'APPLICATION_ERROR'}),
                            content_type='application/json')
    
    admission_project = active_application.admission_project
    project_round = admission_project.get_project_round_for(admission_round)
    is_deadline_passed = project_round.is_deadline_passed()
    
    project_uploaded_document = get_object_or_404(ProjectUploadedDocument,
                                                  pk=document_id)

    if not project_uploaded_document.is_available_for_application(active_application):
        return HttpResponseForbidden()

    if is_deadline_passed and (not project_uploaded_document.is_uploadable_after_deadline(admission_project)):
        return HttpResponseForbidden()
            
    form = UploadedDocumentForm(request.POST, request.FILES)

    is_detail_required = project_uploaded_document.is_detail_required

    upload_kind = get_upload_kind(request, project_uploaded_document)

    if upload_kind == None:
        is_valid, result_code, validation_result = False, 'NO_INPUT', None
    elif upload_kind == 'url':
        is_valid, result_code, validation_result = url_check(form, is_detail_required,
                                                             project_uploaded_document)
    else:
        size_limit = project_uploaded_document.size_limit
        allowed_extentions = [ext.upper() for ext in
                              project_uploaded_document.allowed_extentions.split(',')]

        is_valid, result_code, validation_result = upload_check(form, size_limit, allowed_extentions,
                                                                is_detail_required,
                                                                project_uploaded_document)

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

        if upload_kind == 'url':
            uploaded_document.uploaded_file = ''
        else:
            uploaded_document.document_url = ''
            uploaded_document.orginal_filename = uploaded_document.uploaded_file.name

        error = False
        result_code = 'OK'
        try:
            uploaded_document.save()
            LogItem.create('Uploaded document id %d for %d' % (uploaded_document.id, project_uploaded_document.id), 
                           applicant, request)
        except OperationalError:
            error = True
            result_code = 'DETAIL_ERROR'
        except UnicodeEncodeError:
            error = True
            result_code = 'FILENAME_ERROR'

        if not error:
            from django.template import loader

            template = loader.get_template('appl/include/document_upload_form.html')

            project_uploaded_document.form = upload_form_for(project_uploaded_document)
            project_uploaded_document.applicant_uploaded_documents = project_uploaded_document.get_uploaded_documents_for_applicant(applicant)
            prepare_deadline_flags(project_uploaded_document, admission_project)
            context = {
                'applicant': applicant,
                'project_uploaded_document': project_uploaded_document,
                'toggle': 'show'
            }
            result = {
                'result': 'OK',
                'html': template.render(context, request),
            }
        else:
            result = {'result': result_code}
    else:
        result = {'result': result_code}
        if validation_result is not None:
            result['message_html'] = render_validation_message(project_uploaded_document,
                                                               validation_result,
                                                               request)

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

def encode_or_none(path, encoding):
    try:
        return path.encode(encoding)
    except UnicodeEncodeError:
        return None

def get_file_mime_type(doc_abs_path, buffer=None):
    from magic import Magic

    if not buffer:
        filenames = [doc_abs_path,
                     encode_or_none(doc_abs_path, 'utf8'),
                     encode_or_none(doc_abs_path, 'tis-620')]

        for filename in filenames:
            if filename == None:
                continue
            try:
                buffer = open(filename,"rb").read(1024)
                break
            except:
                continue

    if buffer:
        mime_type = Magic(mime=True).from_buffer(buffer)
        return mime_type
    else:
        return None


def decrypt_content(encrypted_content):
    from cryptography.fernet import Fernet

    key = settings.S3_MEDIA_BACKUP_ENCRYPTION_KEY  # Ensure this key is securely stored and retrieved
    cipher = Fernet(key)

    decrypted_content = cipher.decrypt(encrypted_content)
    return decrypted_content


def download_and_decrypt_file_from_s3(uploaded_document):
    import boto3

    bucket_name = settings.S3_MEDIA_BACKUP_BUCKET_NAME
    aws_access_key = settings.S3_MEDIA_BACKUP_ACCESS_KEY
    aws_secret_key = settings.S3_MEDIA_BACKUP_SECRET_KEY
    endpoint_url = settings.S3_MEDIA_BACKUP_ENDPOINT

    object_name = uploaded_document.encrypted_backup_filename()

    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        endpoint_url=endpoint_url
    )

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_name)
        encrypted_content = response['Body'].read()
        decrypted_content = decrypt_content(encrypted_content)
        return decrypted_content
    except Exception as e:
        return None


def download_uploaded_document_response(uploaded_document):
    doc_file = uploaded_document.uploaded_file
    doc_abs_path = os.path.join(settings.MEDIA_ROOT, doc_file.name)

    mime = get_file_mime_type(doc_abs_path)

    if mime == None:
        content = download_and_decrypt_file_from_s3(uploaded_document)
        if content:
            mime = get_file_mime_type("",buffer=content)
            response = HttpResponse(content)
            response['Content-Type'] = mime
        else:
            return HttpResponseNotFound()
    else:
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

            if active_application == None:
                try:
                    active_application = applicant.accepted_application 
                except:
                    active_application = None
                if active_application:
                    admission_round = active_application.admission_round

            admission_project = active_application.admission_project
            project_round = admission_project.get_project_round_for(admission_round)
            is_deadline_passed = project_round.is_deadline_passed()

            project_uploaded_document = get_object_or_404(ProjectUploadedDocument,pk=project_uploaded_document_id)

            if not project_uploaded_document.is_available_for_application(active_application):
                return HttpResponseForbidden()

            if is_deadline_passed and (not project_uploaded_document.is_uploadable_after_deadline(admission_project)):
                return HttpResponseForbidden()
            
            doc_id = uploaded_document.id
            uploaded_document.delete()
            LogItem.create('Deleted document id %d for %d' % (doc_id, project_uploaded_document.id),
                           applicant, request)


            from django.template import loader
            template = loader.get_template('appl/include/document_upload_form.html')
            project_uploaded_document.form = upload_form_for(project_uploaded_document)
            project_uploaded_document.applicant_uploaded_documents = project_uploaded_document.get_uploaded_documents_for_applicant(applicant_id)
            prepare_deadline_flags(project_uploaded_document, admission_project)

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
