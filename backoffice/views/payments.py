import json

from django import forms
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from admapp.emails import send_payment_email
from appl.models import Payment, AdmissionRound, ProjectApplication
from backoffice.decorators import super_admin_login_required
from regis.models import Applicant, LogItem


class PaymentForm(forms.Form):
    payment_file = forms.FileField()

def  convert_payment_datetime(st):
    from datetime import datetime

    return datetime.strptime(st,'%d%m%Y%H%M%S')


def read_payment_file(f):
    payments = []
    lines = [l.decode('TIS-620','ignore') for l in f.readlines()]
    if lines[0][0] != 'H':
        return []
    
    for l in lines[1:]:
        if l[0] == 'T':
            break

        FIELDS = {'nat_id': (84,20),
                  'ver_num': (104,20),
                  'amount_str': (159,20),
                  'name': (34,50),
                  'paid_at_str': (20,14),
                  'alt_nat_id': (88,13)}

        raw = {}
        for f in FIELDS.keys():
            fr,ln = FIELDS[f]
            raw[f] = l[fr:fr+ln].strip()

        raw['amount'] = float(int(raw['amount_str']))/100000.
        raw['paid_at'] = convert_payment_datetime(raw['paid_at_str'])
        payments.append(raw)

    return payments


def find_applicant(national_id, verification_number, admission_round):
    applicants = Applicant.objects.filter(national_id=national_id)
    if len(applicants) >= 1:
        applicant = applicants[0]
    else:
        return None

    apps = ProjectApplication.objects.filter(applicant=applicant,
                                             admission_round=admission_round).all()

    for a in apps:
        if a.get_verification_number() == verification_number:
            return applicant
        else:
            old_verification_number = a.get_verification_number('80712')
            if old_verification_number == verification_number:
                return applicant

    return None


def find_qr_applicant(qr_national_id):
    #if not qr_national_id.startswith('21'):
    #    return None
    
    #national_id = qr_national_id[2:]
    national_id = qr_national_id
    try:
        applicant = Applicant.objects.get(national_id=national_id)
        return applicant
    except:
        return None

    
def process_payment_file(f):
    from django.conf import settings

    try:
        qr_ref2 = settings.QR_CONFIG['REF2']
    except:
        qr_ref2 = None
    
    payments = read_payment_file(f)
    admission_round = AdmissionRound.get_available()

    MIN_AMOUNT = 51
    MAX_AMOUNT = 999
    
    all_counter = 0
    imported_counter = 0
    ignore_counter = 0
    duplicated_counter = 0
    
    for p in payments:
        all_counter += 1

        if (p['amount'] < MIN_AMOUNT) or (p['amount'] > MAX_AMOUNT):
            ignore_counter += 1
            continue

        payment = Payment(admission_round=admission_round,
                          verification_number=p['ver_num'],
                          national_id=p['nat_id'],
                          payment_name=p['name'],
                          amount=p['amount'],
                          paid_at=p['paid_at'])

        applicant = find_applicant(p['nat_id'], p['ver_num'], admission_round)
        if not applicant and p['nat_id'][1:].startswith('000'):
            applicant = find_qr_applicant(p['alt_nat_id'])

        is_duplicated = False
        if applicant:
            payment.applicant = applicant

            for old_payment in applicant.payment_set.all():
                if (payment.amount == old_payment.amount) and (payment.paid_at == old_payment.paid_at):
                    is_duplicated = True

            if not is_duplicated:
                send_payment_email(applicant, '%.2f' % (p['amount'],),  str(p['paid_at']))
                
                imported_counter += 1
            else:
                duplicated_counter += 1

        if not is_duplicated:
            payment.save()
            
    return 'สามารถนำเข้าได้ {0} ใบ จากทั้งหมด {1} ใบ (มีปัญหา {2} ใบ, ข้าม {3} ใบ, ซ้ำ {4} ใบ)'.format(imported_counter, all_counter, all_counter - imported_counter - duplicated_counter - ignore_counter, ignore_counter, duplicated_counter)
    
@super_admin_login_required
def index(request):
    user = request.user
    if not user.is_super_admin:
        return redirect(reverse('backoffice:index'))

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            msg = process_payment_file(form.cleaned_data['payment_file'])

            request.session['notice'] = msg
            return redirect(reverse('backoffice:payment-index'))
    else:
        form = PaymentForm()

    all_payment_count = Payment.objects.count()
    error_payments = Payment.objects.filter(applicant=None).all()
        
    notice = request.session.pop('notice', None)
        
    return render(request,
                  'backoffice/payments/index.html',
                  { 'notice': notice,
                
                    'form': form,

                    'all_payment_count': all_payment_count,
                    'error_payments': error_payments,
                  })


@super_admin_login_required
def update(request, payment_id):
    from datetime import datetime
    
    user = request.user
    if not user.is_super_admin:
        return HttpResponseForbidden()

    if request.method != 'POST':
        return HttpResponseForbidden()

    payment = get_object_or_404(Payment, pk=payment_id)
    if payment.applicant != None:
        return HttpResponseForbidden()

    result = {'result': 'ERROR'}

    verification_number = request.POST.get('number','').strip()
    if verification_number == '':
        result['msg'] = 'FORM-ERROR'
        application = None
    else:
        application_number = verification_number[:6]
        application = ProjectApplication.find_by_number(application_number)
        if application:
            if application.verification_number != verification_number:
                result['msg'] = 'INCORRECT-VERIFICATION'
                application = None
        else:
            result['msg'] = 'NOT-FOUND'
            
    if application:
        payment.applicant = application.applicant
        payment.has_payment_error = True
        payment.updated_at = datetime.now()
        payment.save()

        send_payment_email(application.applicant, '%.2f' % (payment.amount,), str(payment.paid_at))
        
        LogItem.create('Admin updated payment (id:{0} {1}/{2})'.format(payment_id, payment.national_id, payment.verification_number),
                       application.applicant, request)
            
        result['result'] = 'OK'
        result['full_name'] = application.applicant.get_full_name()

    return HttpResponse(json.dumps(result),
                        content_type='application/json')
