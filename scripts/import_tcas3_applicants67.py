from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from random import choice
from datetime import datetime

from regis.models import Applicant
from appl.models import Major, MajorSelection, ProjectApplication, AdmissionProjectRound, EducationalProfile, AdmissionResult, PersonalProfile, AdmissionProject, AdmissionRound

def random_email():
    return ''.join([choice('abcdefghijklmnopqrstuvwxyz') for i in range(10)]) + '@ku.ac.th'


def read_applicants(filename):
    applicants = []
    with open(filename) as f:
        reader = csv.DictReader(f)
        for items in reader:
            a = {
                'email': items['email'],
                'natid': items['citizen_id'],
                'prefix': items['title'],
                'first_name': items['first_name_th'],
                'last_name': items['last_name_th'],
                'telephone': items['telephone'],
            }
            try:
                a['gpa'] = float(items[4])
            except:
                a['gpa'] = 0

            program_id = items['program_id']
            major_id = items['major_id']
            if major_id != '0':
                full_code = program_id + '0' + major_id
            else:
                full_code = program_id
            a['major_cupt_full_code'] = full_code
            applicants.append(a)
            
    return applicants

def main():
    applicant_filename = sys.argv[1]
    project_id = sys.argv[2]
    round_id = sys.argv[3]

    project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)
    
    applicants = read_applicants(applicant_filename)

    now = datetime.now()
    
    majors = dict([(m.number, m) for m in
                   Major.objects.filter(admission_project=project).all()])
    
    check_dup = False

    counter = 0
    for a in applicants:
        old_apps = Applicant.objects.filter(national_id='x' + a['natid']).all()
        if (len(old_apps) != 0) and check_dup:
            print('ERROR dup', a['natid'])
            continue

        if len(old_apps) != 0:
            app = old_apps[0]
        else:
            app = Applicant()

        app.national_id = 'x' + a['natid']
        app.prefix = a['prefix']
        app.first_name = a['first_name']
        app.last_name = a['last_name']
        app.email = a['email']
        app.random_password()

        print(app)
        app.save()

        if app.project_applications.count() != 0:
            application = app.project_applications.all()[0]
        else:
            application = ProjectApplication()

        application.applicant = app
        application.admission_project = project
        application.admission_round = admission_round
        application.applied_at = now
        
        application.save()

        major_selection = application.get_major_selection()
        if not major_selection:
            major_selection = MajorSelection()

        major_selection.applicant = app
        major_selection.project_application = application
        major_selection.admission_project = project
        major_selection.admission_round = admission_round

        #print(a['major_cupt_full_code'], project)
        major = Major.objects.filter(admission_project=project,
                                     cupt_full_code=a['major_cupt_full_code'])[0]
        
        major_selection.set_majors([major])
        major_selection.save()

        if hasattr(app,'educationalprofile'):
            education = app.educationalprofile
        else:
            education = EducationalProfile()
            education.applicant = app

        education.gpa = a['gpa']
        education.education_level = 1
        education.education_plan = 5
        education.province_id = 1
        education.save()
        
        #print(a['natid'])

        if hasattr(app,'personalprofile'):
            personalprofile = app.personalprofile
        else:
            personalprofile = PersonalProfile()
            personalprofile.applicant = app

        personalprofile.contact_phone = a['telephone']
        personalprofile.mobile_phone = a['telephone']
        personalprofile.birthday = datetime.now()
        personalprofile.save()
        
        old_results = AdmissionResult.objects.filter(application=application,
                                                     admission_project=project,
                                                     admission_round=admission_round).all()
        if len(old_results)!=0:
            result = old_results[0]
        else:
            result = AdmissionResult(application=application,
                                     admission_project=project,
                                     admission_round=admission_round)
        result.applicant=app
        result.major_rank=1
        result.major=major

        result.is_accepted_for_interview = True
        result.updated_accepted_for_interview_at = datetime.now()
        result.save()
        
        counter += 1
        if counter % 1000 == 0:
            print(counter, a['natid'])
            

if __name__ == '__main__':
    main()
