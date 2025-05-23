from django_bootstrap import bootstrap
bootstrap()

import sys

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication, Payment, AdmissionResult, Major
from backoffice.models import CheckMarkGroup

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


def load_check_marks(applicant, admission_project):
    groups = (CheckMarkGroup
              .objects
              .select_related('project_application')
              .filter(project_application__admission_project=admission_project)
              .filter(applicant=applicant)
              .all())
    if len(groups) > 0:
        return groups[0]
    else:
        return None    

def print_applicant_info(applicant, major_numbers, admission_project, 
                         has_multimajor_criteria_check=False):
    project_criteria_passed = True
    if has_multimajor_criteria_check:
        check_marks = load_check_marks(applicant, admission_project)
        if check_marks:
            project_criteria_passed = check_marks.is_multimajor_criteria_passed

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
    for m in major_numbers:
        major = Major.objects.filter(admission_project=admission_project, number=m).first()
        result = AdmissionResult.objects.filter(applicant=applicant, major=major).first()
        if result:
            if project_criteria_passed == False:
                items.append('False')
            else:
                items.append(str(result.is_criteria_passed))
        else:
            items.append('None')

    print(','.join(items))

EXTRA_NAT_ID = [
]

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)
    project_round = admission_project.get_project_round_for(admission_round)

    applicants = ProjectApplication.objects.filter(admission_project=admission_project,
                                                   admission_round=admission_round,
                                                   is_canceled=False).all()

    amount_paid = compute_amount_paid(admission_round)
    for nid in EXTRA_NAT_ID:
        amount_paid[nid] = 100000
    
    for app in applicants:
        national_id = app.applicant.national_id
        majors = app.get_major_selection()
        if not majors:
            continue

        if national_id not in amount_paid:
            amount_paid[national_id] = 0

        admission_fee = app.admission_fee(major_selection=majors)
        if amount_paid[national_id] < admission_fee:
            continue

        print_applicant_info(app.applicant, 
                             majors.get_major_numbers(), 
                             admission_project,
                             project_round.multimajor_criteria_check_required)

    
if __name__ == '__main__':
    main()
    
