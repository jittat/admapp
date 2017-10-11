from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, MultiWidgetField, Div, Row

from regis.models import Applicant
from appl.models import Payment, AdmissionRound, ProjectApplication
from backoffice.models import Profile

from admapp.emails import send_payment_email

from .permissions import is_super_admin

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
                  'paid_at_str': (20,14)}

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
    if len(applicants) >= 0:
        applicant = applicants[0]
    else:
        return None

    apps = ProjectApplication.objects.filter(applicant=applicant,
                                             admission_round=admission_round).all()

    for a in apps:
        if a.get_verification_number() == verification_number:
            return applicant

    return None

def process_payment_file(f):
    payments = read_payment_file(f)
    admission_round = AdmissionRound.get_available()

    all_counter = 0
    imported_counter = 0
    for p in payments:
        payment = Payment(admission_round=admission_round,
                          verification_number=p['ver_num'],
                          national_id=p['nat_id'],
                          payment_name=p['name'],
                          amount=p['amount'],
                          paid_at=p['paid_at'])

        applicant = find_applicant(p['nat_id'], p['ver_num'], admission_round)
        if applicant:
            payment.applicant = applicant

            send_payment_email(applicant, '%.2f' % (p['amount'],),  str(p['paid_at']))
            
            imported_counter += 1
            
        payment.save()
        all_counter += 1
    return 'สามารถนำเข้าได้ {0} ใบ จากทั้งหมด {1} ใบ (มีปัญหา {2} ใบ)'.format(imported_counter, all_counter, all_counter - imported_counter)
    
@login_required
def index(request):
    user = request.user
    if not is_super_admin(user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            msg = process_payment_file(form.cleaned_data['payment_file'])

            request.session['notice'] = msg
            return redirect(reverse('backoffice:payment-index'))
    else:
        form = PaymentForm()

    error_payments = Payment.objects.filter(applicant=None).all()
        
    notice = request.session.pop('notice', None)
        
    return render(request,
                  'backoffice/payments/index.html',
                  { 'is_super_admin': is_super_admin(user),

                    'notice': notice,

                    'form': form,

                    'error_payments': error_payments,
                  })
