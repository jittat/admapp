from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication, Payment
from supplements.models import load_supplement_configs_with_instance

import json

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


def extract_with(obj, fmap):
    out = {}
    for f in fmap.keys():
        if f.startswith('$'):
            ff = fmap[f]
            out[ff] = str(getattr(obj,f[1:]))
        else:
            ff = fmap[f]
            out[ff] = getattr(obj,f)
    return out

EDUPLAN_MAP = {
    1: 1,
    2: 2,
    3: 3,
    4: 5,
    5: 5,
    6: 4,
}

def extract_education(applicant):
    education = applicant.educationalprofile
    data = extract_with(education, {'education_level': 'edu_type',
                                    'education_plan': 'study_plan',
                                    'gpa': 'gpa',
                                    'school_title': 'school_name',
                                    '$province': 'school_province'})
    data['study_plan'] = EDUPLAN_MAP[data['study_plan']]
    return data
    
def extract_applicant(applicant):
    return extract_with(applicant, {'id': 'id',
                                    'national_id': 'national_id',
                                    'email': 'email',
                                    'prefix': 'title',
                                    'first_name': 'firstname',
                                    'last_name': 'lastname'})


def extract_applicant_info(applicant, admission_project):
    supplements = load_supplement_configs_with_instance(applicant, admission_project)
    
    return { 'applicant': extract_applicant(applicant),
             'edu': extract_education(applicant),
             'supplements': dict([(s.name, json.loads(s.supplement_instance.json_data))
                                  for s in supplements]) }

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    applicants = ProjectApplication.objects.filter(admission_project=admission_project,
                                                   admission_round=admission_round,
                                                   is_canceled=False).order_by('applicant_id').all()

    amount_paid = compute_amount_paid(admission_round)

    data = []
    
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

        data.append(extract_applicant_info(app.applicant, admission_project))

    print(json.dumps(data, indent=1))

    
if __name__ == '__main__':
    main()
    
