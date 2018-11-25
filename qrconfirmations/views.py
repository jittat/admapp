from django.shortcuts import render

from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import dateutil.parser

from .models import QRConfirmation
from appl.models import AdmissionRound, Payment, Applicant

def health(request):
    return JsonResponse({ 'description': 'KU Admission Health Status',
                          'status': 'UP' })

def extract_national_id(ref1):
    if ref1.startswith('21'):
        return ref1[2:]
    else:
        return ''

def process_payment(ref1, ref2, amount, transaction_date_and_time):
    national_id = extract_national_id(ref1)
    if national_id == '':
        return False

    admission_round = AdmissionRound.get_available()
    if not admission_round:
        return False

    try:
        paid_at = dateutil.parser.parse(transaction_date_and_time, ignoretz=True)
    except:
        paid_at = datetime.now()

    applicants = Applicant.objects.filter(national_id=national_id)
    if len(applicants) >= 1:
        applicant = applicants[0]
    else:
        applicant = None
        
    payment = Payment(admission_round=admission_round,
                      applicant=applicant,
                      verification_number=ref2,
                      national_id=national_id,
                      amount=amount,
                      paid_at=paid_at)
    payment.save()
    
    return True

@csrf_exempt
def sent(request):
    #if request.method != 'POST':
    #    return HttpResponseForbidden()

    confirm_id = settings.QR_CONFIG['CONFIRM_ID']
    if request.body:
        json_data = json.loads(request.body.decode('utf-8'))

        ref1 = json_data.get('billPaymentRef1', '')
        ref2 = json_data.get('billPaymentRef2', '')
        amount = json_data.get('amount', '0.00')
        transaction_date_and_time = json_data.get('transactionDateandTime', '')

        success = process_payment(ref1, ref2, amount, transaction_date_and_time)
        
        confirmation = QRConfirmation(bill_payment_ref1=ref1,
                                      bill_payment_ref2=ref2,
                                      remote_addr=request.META.get('REMOTE_ADDR',''),
                                      body=request.body)

        if success:
            confirmation.status = 0
        else:
            confirmation.status = 500

        confirmation.save()
        
        transaction_id = json_data.get('transactionId','')

        return JsonResponse({ 'resCode': '00',
                              'resDesc': 'success',
                              'transactionId': transaction_id,
                              'confirm_id': confirm_id })

    else:
        return JsonResponse({ 'resCode': '99',
                              'resDesc': 'failed',
                              'transactionId': '',
                              'confirm_id': confirm_id })

        
