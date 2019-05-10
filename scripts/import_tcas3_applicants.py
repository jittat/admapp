from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from random import choice
from datetime import datetime

from regis.models import Applicant
from appl.models import Major, MajorSelection, ProjectApplication, AdmissionProjectRound, EducationalProfile

def random_email():
    return ''.join([choice('abcdefghijklmnopqrstuvwxyz') for i in range(10)]) + '@ku.ac.th'


def read_applicants(filename):
    applicants = []
    with open(filename) as f:
        reader = csv.reader(f)
        for items in reader:
            a = {
                'natid': items[0],
                'prefix': items[1],
                'first_name': items[2],
                'last_name': items[3],
            }
            try:
                a['gpa'] = float(items[4])
            except:
                a['gpa'] = 0
            a['majors'] = [int(x) for x in items[6:]]
            applicants.append(a)
            
    return applicants

def main():
    applicant_filename = sys.argv[1]
    project_round_id = sys.argv[2]

    project_round = AdmissionProjectRound.objects.get(pk=project_round_id)
    project = project_round.admission_project
    admission_round = project_round.admission_round
    
    applicants = read_applicants(applicant_filename)

    now = datetime.now()
    
    majors = dict([(m.number, m) for m in
                   Major.objects.filter(admission_project=project).all()])
    
    check_dup = False

    counter = 0
    for a in applicants:
        old_apps = Applicant.objects.filter(national_id=a['natid']).all()
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
        app.email = random_email()
        app.random_password()

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
        major_selection.set_majors([majors[num]
                                    for num
                                    in a['majors']])
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

        counter += 1
        if counter % 1000 == 0:
            print(counter, a['natid'])
            

if __name__ == '__main__':
    main()
