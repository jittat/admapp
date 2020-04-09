from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse, HttpResponseServerError

from regis.models import Applicant, LogItem
from regis.models import CuptConfirmation, CuptRequestQueueItem

from regis.decorators import appl_login_required

from admapp.utils import number_to_thai_text

from appl.models import AdmissionProject, AdmissionRound, AdmissionProjectRound
from appl.models import ProjectApplication
from appl.models import ProjectUploadedDocument
from appl.models import Eligibility
from appl.models import Payment
from appl.models import AdmissionResult, MajorInterviewDescription

from appl.views.upload import upload_form_for

from appl.barcodes import generate
from appl.qrpayment import generate_ku_qr

from supplements.models import load_supplement_configs_with_instance

def prepare_uploaded_document_forms(applicant, project_uploaded_documents):
    for d in project_uploaded_documents:
        d.form = upload_form_for(d)
        d.applicant_uploaded_documents = d.get_uploaded_documents_for_applicant(applicant)


def prepare_project_eligibility_and_detes(projects,
                                          admission_round,
                                          applicant):
    for project in projects:
        project.eligibility = Eligibility.check(project, applicant)
        project.project_round = project.get_project_round_for(admission_round)


def load_supplement_blocks(request, applicant, admission_project, admission_round):
    from supplements.models import PROJECT_ADDITIONAL_BLOCKS
    from supplements.views import render_supplement_block
    
    supplement_blocks = []
    if admission_project.short_title in PROJECT_ADDITIONAL_BLOCKS:
        for config in PROJECT_ADDITIONAL_BLOCKS[admission_project.short_title]:
            supplement_blocks.append(render_supplement_block(request,
                                                             applicant,
                                                             admission_project,
                                                             admission_round,
                                                             config))
    return supplement_blocks    

def check_project_documents(applicant,
                            admission_project,
                            supplement_configs,
                            project_uploaded_documents):
    status = True
    errors = []

    for d in project_uploaded_documents:
        if d.is_required and len(d.applicant_uploaded_documents) == 0:
            status = False
            errors.append('ยังไม่ได้อัพโหลด' + d.title)

    for c in supplement_configs:
        if callable(c.is_required):
            is_required = c.is_required(applicant,
                                        admission_project,
                                        c)
        else:
            is_required = c.is_required
        if is_required and (not c.supplement_instance):
            status = False
            errors.append('ยังไม่ได้ป้อนข้อมูล' + c.title)
            
    return { 'status': status,
             'errors': errors }

def load_applications_in_other_round(applicant, current_admission_round):
    admission_rounds = AdmissionRound.objects.filter(is_application_available=True).all()
    results = []
    for a in admission_rounds:
        if a.id != current_admission_round.id:
            active_application = applicant.get_active_application(a)
            if active_application:
                results.append((a, active_application))
    return results

def index_outside_round(request):
    return HttpResponseForbidden()


def is_payment_deadline_passed(deadline):
    return datetime.now() > datetime(deadline.year, deadline.month, deadline.day) + timedelta(days=1)

def index_with_active_application(request, active_application, admission_round=None):
    applicant = request.applicant
    if not admission_round:
        admission_round = AdmissionRound.get_available()
        
    admission_project = active_application.admission_project

    project_round = admission_project.get_project_round_for(admission_round)
    is_deadline_passed = project_round.is_deadline_passed()
    payment_deadline = project_round.payment_deadline
    payment_deadline_passed = is_payment_deadline_passed(payment_deadline)
    
    common_uploaded_documents = ProjectUploadedDocument.get_common_documents()
    project_uploaded_documents = admission_project.projectuploadeddocument_set.all()
    
    prepare_uploaded_document_forms(applicant, common_uploaded_documents)
    prepare_uploaded_document_forms(applicant, project_uploaded_documents)

    major_selection = active_application.get_major_selection()

    supplement_configs = load_supplement_configs_with_instance(applicant,
                                                               admission_project)

    supplement_blocks = load_supplement_blocks(request,
                                               applicant,
                                               admission_project,
                                               admission_round)
    
    admission_fee = active_application.admission_fee(major_selection)
    payments = Payment.find_for_applicant_in_round(applicant, admission_round)
    paid_amount = sum([p.amount for p in payments])

    if admission_fee > paid_amount:
        additional_payment = admission_fee - paid_amount
    else:
        additional_payment = 0

    documents_complete_status = check_project_documents(applicant,
                                                        admission_project,
                                                        supplement_configs,
                                                        list(common_uploaded_documents) + list(project_uploaded_documents))
        
    admission_projects = []
    has_confirmed = False
    
    if project_round.accepted_for_interview_result_shown:
        admission_results = AdmissionResult.find_by_application(active_application)
        is_accepted_for_interview = False
        is_accepted = False
        accepted_result = None
        interview_descriptions = None

        for res in admission_results:
            if res.is_accepted_for_interview:
                is_accepted_for_interview = True
                if res.is_accepted:
                    is_accepted = True
                    accepted_result = res

                    if res.has_confirmed:
                        has_confirmed = True

        mresults = dict([(res.major_id, res) for res in admission_results])
        if major_selection:
            for major in major_selection.get_majors():
                if major.id not in mresults:
                    major.is_accepted_for_interview = False
                else:
                    major.is_accepted_for_interview = mresults[major.id].is_accepted_for_interview
                    if major.is_accepted_for_interview:
                        interview_descriptions = (
                            MajorInterviewDescription.find_by_major_and_admission_round(major,
                                                                                        admission_round))

    else:
        admission_results = []
        is_accepted_for_interview = False
        interview_descriptions = None
        is_accepted = False
        accepted_result = None

    other_application_rounds = load_applications_in_other_round(applicant,
                                                                admission_round)
    notice = request.session.pop('notice', None)

    # HACK for sport options
    log_key = LogItem.generate_log_key(applicant)
    last_log = LogItem.get_applicant_latest_log(applicant,
                                                'appllog:sport-confirm-option')
    if not last_log:
        sport_option = '0'
    else:
        sport_option = last_log.message[-1]

    return render(request,
                  'appl/index.html',
                  { 'notice': notice,
                    'applicant': applicant,

                    'other_application_rounds': other_application_rounds,
                    
                    'is_deadline_passed': is_deadline_passed,
                    
                    'personal_profile': applicant.get_personal_profile(),
                    'educational_profile': applicant.get_educational_profile(),
                    'common_uploaded_documents': common_uploaded_documents,
                    'project_uploaded_documents': project_uploaded_documents,

                    'admission_round': admission_round,
                    'admission_projects': admission_projects,
                    'project_round': project_round,
                    'active_application': active_application,
                    'supplement_configs': supplement_configs,
                    'supplement_blocks': supplement_blocks,
                    
                    'major_selection': major_selection,

                    'documents_complete_status': documents_complete_status,
                    
                    'payments': payments,
                    'paid_amount': paid_amount,
                    'additional_payment': additional_payment,
                    'payment_deadline': payment_deadline,
                    'payment_deadline_passed': payment_deadline_passed,

                    'accepted_for_interview_result_shown': project_round.accepted_for_interview_result_shown,
                    'admission_results': admission_results,
                    'is_accepted_for_interview': is_accepted_for_interview,
                    'interview_descriptions': interview_descriptions,

                    'accepted_result_shown': project_round.accepted_result_shown,
                    'is_accepted': is_accepted,
                    'accepted_result': accepted_result,
                    'has_confirmed': has_confirmed,

                    'log_key': log_key,
                    'sport_option': sport_option,
                  })


@appl_login_required
def index(request, admission_round_id='0'):
    applicant = request.applicant

    if applicant.confirmed_application:
        active_application = applicant.confirmed_application
        admission_round = active_application.admission_round
        return index_with_active_application(request, active_application, admission_round)

    if admission_round_id == '0':
        admission_round = AdmissionRound.get_available()
    else:
        admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)

    if not admission_round:
        return index_outside_round(request)

    personal_profile = applicant.get_personal_profile()
    if not personal_profile:
        return redirect(reverse('appl:personal-profile'))
    
    educational_profile = applicant.get_educational_profile()
    if not educational_profile:
        return redirect(reverse('appl:education-profile'))
    
    active_application = applicant.get_active_application(admission_round)

    if active_application:
        return index_with_active_application(request, active_application, admission_round)

    common_uploaded_documents = ProjectUploadedDocument.get_common_documents()
    prepare_uploaded_document_forms(applicant, common_uploaded_documents)

    admission_projects = []
    active_application = None
    major_selection = None
    payments = []
    paid_amount = 0
    additional_payment = 0
    supplement_configs = []
    
    admission_projects = admission_round.get_available_projects()

    if getattr(settings,'VERIFY_CUPT_CONFIRMATION',False):
        if applicant.has_cupt_confirmation_result():
            cupt_confirmation_status = applicant.cupt_confirmation.get_status()
        else:
            CuptRequestQueueItem.create_for(applicant)
            cupt_confirmation_status = CuptConfirmation.get_wait_status()
    else:
        cupt_confirmation_status = CuptConfirmation.get_not_required_status()
    
    prepare_project_eligibility_and_detes(admission_projects,
                                          admission_round,
                                          applicant)

    admission_projects = [a[2] for a in
                          sorted([({True: 1, False: 0}[p.is_deadline_passed()],
                                   p.id, p) for p in admission_projects])]
    
    admission_fee = 0
    payments = Payment.find_for_applicant_in_round(applicant, admission_round)
    paid_amount = sum([p.amount for p in payments])
    additional_payment = 0

    other_application_rounds = load_applications_in_other_round(applicant,
                                                                admission_round)

    # TODO: fix this hack
    #if len(other_application_rounds) != 0:
    #    return redirect(reverse('appl:index-with-round', args=[other_application_rounds[0][0].id]))

    notice = request.session.pop('notice', None)

    return render(request,
                  'appl/index.html',
                  { 'notice': notice,
                    'applicant': applicant,
                    'personal_profile': personal_profile,
                    'educational_profile': educational_profile,

                    'other_application_rounds': other_application_rounds,
                    
                    'common_uploaded_documents': common_uploaded_documents,

                    'admission_round': admission_round,
                    'admission_projects': admission_projects,
                    'active_application': active_application,
                    'supplement_configs': supplement_configs,
                    'major_selection': major_selection,

                    'cupt_confirmation_status': cupt_confirmation_status,
                    
                    'payments': payments,
                    'paid_amount': paid_amount,
                    'additional_payment': additional_payment,
                  })

        
@appl_login_required
def apply_project(request, project_id, admission_round_id):
    applicant = request.applicant
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)

    project_round = project.get_project_round_for(admission_round)
    if not project_round:
        return HttpResponseForbidden()

    if not project_round.is_open():
        return redirect(reverse('appl:index'))
    
    active_application = applicant.get_active_application(admission_round)
    
    if active_application:
        return HttpResponseForbidden()

    eligibility = Eligibility.check(project, applicant)
    if not eligibility.is_eligible:
        return HttpResponseForbidden()
    
    application = applicant.apply_to_project(project, admission_round)

    LogItem.create('Applied to project %d' % (project.id,), applicant, request)
    
    return redirect(reverse('appl:index'))


@appl_login_required
def cancel_project(request, project_id, admission_round_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    if 'ok' not in request.POST:
        return redirect(reverse('appl:index'))
    
    applicant = request.applicant
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)

    project_round = project.get_project_round_for(admission_round)
    if (not project_round) or (not project_round.is_open()):
        return redirect(reverse('appl:index'))
    
    active_application = applicant.get_active_application(admission_round)
    
    if ((not active_application) or
        (active_application.admission_project.id != project.id) or
        (active_application.admission_round.id != admission_round.id)):
        return redirect(reverse('appl:index'))

    active_application.is_canceled = True
    active_application.cancelled_at = datetime.now()
    active_application.save()
    
    LogItem.create('Canceled application to project %d' % (project.id,), applicant, request)

    return redirect(reverse('appl:index'))


@appl_login_required
def cancel_project_special(request, project_id, admission_round_id):
    return redirect(reverse('appl:index'))

    if request.method != 'POST':
        return HttpResponseForbidden()

    if 'ok' not in request.POST:
        return redirect(reverse('appl:index'))
    
    applicant = request.applicant
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)

    project_round = project.get_project_round_for(admission_round)
    if (not project_round) or (admission_round.number != 2):
        return redirect(reverse('appl:index'))
    
    active_application = applicant.get_active_application(admission_round)
    
    if ((not active_application) or
        (active_application.admission_project.id != project.id) or
        (active_application.admission_round.id != admission_round.id)):
        return redirect(reverse('appl:index'))

    active_application.is_canceled = True
    active_application.cancelled_at = datetime.now()
    active_application.save()
    
    LogItem.create('Special canceled application to project %d' % (project.id,), applicant, request)

    return redirect(reverse('appl:index'))


def random_barcode_stub():
    from random import randint
    return str(1000000 + randint(1,8000000))


@appl_login_required
def payment(request, application_id, payment_type=''):
    applicant = request.applicant
    application = get_object_or_404(ProjectApplication, pk=application_id)

    if application.applicant_id != applicant.id:
        return HttpResponseForbidden()

    admission_round = application.admission_round
    admission_project = application.admission_project
    major_selection = application.major_selection
    
    admission_fee = application.admission_fee(major_selection)

    payments = Payment.find_for_applicant_in_round(applicant, admission_round)
    paid_amount = sum([p.amount for p in payments])

    if admission_fee > paid_amount:
        additional_payment = admission_fee - paid_amount
    else:
        additional_payment = 0

    project_round = admission_project.get_project_round_for(admission_round)
    if not project_round:
        return redirect(reverse('appl:index'))

    deadline = project_round.payment_deadline

    if payment_type == '':
        LogItem.create('Printed payment form (amount: %d)' % (additional_payment,),
                       applicant, request)
    
        return render(request,
                      'appl/payments/payment.html',
                      { 'applicant': applicant,

                        'application': application,
                        'admission_round': admission_round,
                        'admission_project': admission_project,
                        'major_selection': major_selection,
                        
                        'payment_amount': additional_payment,
                        'payment_str': number_to_thai_text(int(additional_payment)) + 'บาทถ้วน',

                        'deadline': deadline,
                        'barcode_stub': random_barcode_stub(),
                      })
    else:
        if is_payment_deadline_passed(deadline):
            return redirect(reverse('appl:index'))
        
        LogItem.create('Printed QR payment form (amount: %d)' % (additional_payment,),
                       applicant, request)
    
        return render(request,
                      'appl/payments/payment_qr.html',
                      { 'applicant': applicant,

                        'application': application,
                        'admission_round': admission_round,
                        'admission_project': admission_project,
                        'major_selection': major_selection,
                        
                        'payment_amount': additional_payment,
                        'payment_str': number_to_thai_text(int(additional_payment)) + 'บาทถ้วน',
                        
                        'deadline': deadline,
                        'barcode_stub': random_barcode_stub(),
                      })


def payment_with_qr_code(request, application_id):
    #return HttpResponseForbidden()
    return payment(request, application_id, 'qr')

def payment_code_img(request, application_id, stub, code_type):
    applicant = request.applicant
    application = get_object_or_404(ProjectApplication, pk=application_id)

    if application.applicant_id != applicant.id:
        return HttpResponseForbidden()

    admission_fee = application.admission_fee()
    admission_round = application.admission_round

    payments = Payment.find_for_applicant_in_round(applicant, admission_round)
    paid_amount = sum([p.amount for p in payments])

    if admission_fee > paid_amount:
        additional_payment = admission_fee - paid_amount
    else:
        additional_payment = 0


    import os.path
    
    img_filename = os.path.join(settings.BARCODE_DIR,
                                applicant.national_id + '-' +
                                str(application.id) + '-' +
                                stub)

    generated = False
    if code_type == 'barcode':
        generate('099400015938201',
                 applicant.national_id,
                 application.get_verification_number(),
                 additional_payment,
                 img_filename)
        generated = True
    else:
        generated = generate_ku_qr(applicant,
                                   application,
                                   additional_payment,
                                   img_filename)


    if generated:
        fp = open(img_filename + '.png', 'rb')
        response = HttpResponse(fp)
        response['Content-Type'] = 'image/png'
        return response
    else:
        return HttpResponseServerError()


@appl_login_required
def payment_barcode(request, application_id, stub):
    return payment_code_img(request, application_id, stub, 'barcode')


@appl_login_required
def payment_qrcode(request, application_id, stub):
    return payment_code_img(request, application_id, stub, 'qrcode')


@appl_login_required
def check_application_documents(request):
    applicant = request.applicant
    admission_round = AdmissionRound.get_available()
    active_application = applicant.get_active_application(admission_round)

    if not active_application:
        return HttpResponseForbidden()

    admission_project = active_application.admission_project
    project_round = admission_project.get_project_round_for(admission_round)
    payment_deadline = project_round.payment_deadline
    
    admission_project = active_application.admission_project
    
    common_uploaded_documents = ProjectUploadedDocument.get_common_documents()
    project_uploaded_documents = admission_project.projectuploadeddocument_set.all()
    
    prepare_uploaded_document_forms(applicant, common_uploaded_documents)
    prepare_uploaded_document_forms(applicant, project_uploaded_documents)

    major_selection = active_application.get_major_selection()

    supplement_configs = load_supplement_configs_with_instance(applicant,
                                                               admission_project)

    documents_complete_status = check_project_documents(applicant,
                                                        admission_project,
                                                        supplement_configs,
                                                        list(common_uploaded_documents) + list(project_uploaded_documents))
        
    admission_fee = active_application.admission_fee(major_selection)

    payments = Payment.find_for_applicant_in_round(applicant, admission_round)
    paid_amount = sum([p.amount for p in payments])

    if admission_fee > paid_amount:
        additional_payment = admission_fee - paid_amount
    else:
        additional_payment = 0

    return render(request,
                  'appl/include/application_document_status.html',
                  { 'documents_complete_status': documents_complete_status,
                    'active_application': active_application,
                    'major_selection': major_selection,
                    
                    'payments': payments,
                    'paid_amount': paid_amount,
                    'additional_payment': additional_payment,
                    'payment_deadline': payment_deadline,
                    })


@appl_login_required
def get_additional_payment(request):
    applicant = request.applicant
    admission_round = AdmissionRound.get_available()
    active_application = applicant.get_active_application(admission_round)

    if not active_application:
        return HttpResponseForbidden()

    major_selection = active_application.get_major_selection()
    admission_fee = active_application.admission_fee(major_selection)

    payments = Payment.find_for_applicant_in_round(applicant, admission_round)
    paid_amount = sum([p.amount for p in payments])

    if admission_fee > paid_amount:
        additional_payment = admission_fee - paid_amount
    else:
        additional_payment = 0

    return JsonResponse({ 'additionalPayment': additional_payment })
