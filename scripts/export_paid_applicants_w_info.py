from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication, Payment

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


def print_applicant_info(applicant, major_numbers):
    items = ['"%s"' % applicant.national_id, applicant.get_full_name()]
    education = applicant.educationalprofile
    items.append('%.3f' % education.gpa)
    items.append(str(education.education_plan))
    items.append(str(education.get_education_plan_display()))
    items.append(str(education.province.id))
    items.append(education.province.title)
    items.append(str(len(major_numbers)))
    for num in major_numbers:
        items.append(str(num))
    print(','.join(items))


def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    applicants = ProjectApplication.objects.filter(admission_project=admission_project,
                                                   admission_round=admission_round,
                                                   is_canceled=False).all()

    amount_paid = compute_amount_paid(admission_round)
    
    for app in applicants:
        national_id = app.applicant.national_id
        majors = app.get_major_selection()
        if not majors:
            continue

        if national_id not in amount_paid:
            continue

        admission_fee = app.admission_fee(major_selection=majors)
        if amount_paid[national_id] < admission_fee:
            continue

        print_applicant_info(app.applicant, majors.get_major_numbers())

    
if __name__ == '__main__':
    main()
    
