from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication, Payment
from admapp.emails import send_major_confirmation_email

def compute_amount_paid(admission_round):
    payments = Payment.objects.filter(admission_round=admission_round).all()

    amount_paid = {}
    for p in payments:
        if p.applicant == None:
            continue
        nat_id = p.applicant.national_id
        if nat_id not in amount_paid:
            amount_paid[nat_id] = p.amount
        else:
            amount_paid[nat_id] += p.amount

    return amount_paid


def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    applications = ProjectApplication.objects.filter(admission_project=admission_project,
                                                     admission_round=admission_round,
                                                     is_canceled=False).all()

    amount_paid = compute_amount_paid(admission_round)
    
    for app in applications:
        national_id = app.applicant.national_id
        if national_id not in amount_paid:
            continue

        majors = app.get_major_selection()
        if not majors:
            print('ERROR major not found:', str(app.applicant))
            continue

        admission_fee = app.admission_fee(major_selection=majors)
        if amount_paid[national_id] < admission_fee:
            continue

        send_major_confirmation_email(app.applicant, app, majors.get_majors())
        print(app.applicant)
    
if __name__ == '__main__':
    main()
    
