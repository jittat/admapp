from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from django.contrib.auth.models import User
from appl.models import AdmissionProject, Faculty

def main():
    filename = sys.argv[1]
    counter = 0
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        first = True
        for items in reader:
            if first:
                first = False
                continue

            if len(items) < 5:
                continue
            username = items[0]
            email = username + '@fake.admission.ku.ac.th'
            password = items[2]

            user = User.objects.create_user(username, email, password)

            user.first_name = items[1]
            user.save()

            project = AdmissionProject.objects.get(pk=items[3])
            faculty = Faculty.objects.get(pk=items[4])

            profile = user.profile
            profile.is_admission_admin = False
            profile.admission_projects.add(project)
            profile.faculty = faculty
            profile.save()

            counter += 1

    print('Imported',counter,'users')
        

if __name__ == '__main__':
    main()
    
