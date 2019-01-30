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

            if len(items) < 6:
                continue
            username = items[0].strip()

            if username == "":
                continue
            
            email = username + '@fake.admission.ku.ac.th'
            password = items[3]

            old_user = User.objects.filter(username=username)
            if len(old_user) >= 1:
                user = old_user[0]
                user.email = email
                user.set_password(password)
            else:
                user = User.objects.create_user(username, email, password)

            user.first_name = items[1].strip()
            user.last_name = items[2].strip()
            user.save()

            profile = user.profile
            profile.is_admission_admin = False
            profile.is_number_adjustment_admin = True
            
            profile.major_number = int(items[4])
            faculty_title = items[5]
            if ' ' in items[5]:
                faculty_title = ' '.join(items[5].split()[1:])

            profile.faculty = Faculty.objects.get(title=faculty_title)
            
            profile.save()

            print(username)

            counter += 1

    print('Imported',counter,'users')
        

if __name__ == '__main__':
    main()
    
