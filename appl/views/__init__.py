from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from regis.models import Applicant
from regis.decorators import appl_login_required

from appl.models import AdmissionProject, ProjectUploadedDocument, AdmissionRound, Payment, ProjectApplication

from appl.views.upload import upload_form_for

def prepare_uploaded_document_forms(applicant, project_uploaded_documents):
    for d in project_uploaded_documents:
        d.form = upload_form_for(d)
        d.applicant_uploaded_documents = d.get_uploaded_documents_for_applicant(applicant)


def load_applicant_application(applicant, admission_round):
    active_application = applicant.get_active_application(admission_round)
    try:
        major_selection = active_application.major_selection
    except:
        major_selection = None

    payments = Payment.find_for_applicant_in_round(applicant, admission_round)

    return active_application, major_selection, payments
    
        
@appl_login_required
def index(request):
    applicant = request.applicant
    
    common_uploaded_documents = ProjectUploadedDocument.get_common_documents()
    prepare_uploaded_document_forms(applicant, common_uploaded_documents)

    admission_round = AdmissionRound.get_available()
    if admission_round:
        admission_projects = admission_round.get_available_projects()

        active_application, major_selection, payments = load_applicant_application(applicant, admission_round)

        if active_application:
            admission_fee = active_application.admission_fee(major_selection)
        else:
            admission_fee = 0

        payments = Payment.find_for_applicant_in_round(applicant, admission_round)
        paid_amount = sum([p.amount for p in payments])

        if admission_fee > paid_amount:
            additional_payment = admission_fee - paid_amount
        else:
            additional_payment = 0
    else:
        admission_projects = []
        active_application = None
        major_selection = None
        payments = []
        paid_amount = 0
        additional_payment = 0
        
    return render(request,
                  'appl/index.html',
                  { 'applicant': applicant,
                    'common_uploaded_documents': common_uploaded_documents,

                    'admission_round': admission_round,
                    'admission_projects': admission_projects,
                    'active_application': active_application,
                    'major_selection': major_selection,

                    'payments': payments,
                    'paid_amount': paid_amount,
                    'additional_payment': additional_payment,
                  })

        
@appl_login_required
def apply_project(request, project_id, admission_round_id):
    applicant = request.applicant
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=admission_round_id)
    
    active_application = applicant.get_active_application(admission_round)
    
    if active_application:
        return redirect(reverse('appl:index'))

    application = applicant.apply_to_project(project, admission_round)
    return redirect(reverse('appl:index'))
    

@appl_login_required
def payment(request, application_id):
    applicant = request.applicant
    application = get_object_or_404(ProjectApplication, pk=application_id)

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

    return render(request,
                  'appl/payments/payment.html',
                  { 'applicant': applicant,

                    'application': application,
                    'admission_round': admission_round,
                    'admission_project': admission_project,
                    'major_selection': major_selection,

                    'payment_amount': additional_payment,

                    'deadline': 'ลืมไปเลยว่าผมเคยเสีย',
                  })

