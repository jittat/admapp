from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import io
import json

from qrconfirmations.models import QRConfirmation
from appl.models import AdmissionRound, Payment, Applicant

from qrconfirmations.views import process_payment

def main():
    for confirmation in QRConfirmation.objects.all():
        if confirmation.payment == None:
            #print("---" + eval(confirmation.body).decode('utf-8') + "---")
            json_data = json.loads(eval(confirmation.body).decode('utf-8'))

            ref1 = json_data.get('ref1Prefix','')
            ref2 = json_data.get('ref2Prefix','')
            amount = json_data.get('amount', '0.00')

            transaction_date_and_time = ''

            payment = process_payment(ref1, ref2, amount, transaction_date_and_time)

            if payment:
                confirmation.payment = payment
                confirmation.status = 100
                confirmation.save()
                print('Saved', payment.applicant)
            else:
                print('Error', json_data)
        

if __name__ == '__main__':
    main()
    
