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
                'natid': 'x' + items[0],
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
    applicants = read_applicants(applicant_filename)

    counter = 0
    for a in applicants:
        old_apps = Applicant.objects.filter(national_id=a['natid']).all()
        if len(old_apps) == 0:
            continue

        app = old_apps[0]

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
