from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import io

from appl.models import ProjectApplication

def main():
    applications = ProjectApplication.objects.all()

    counter = 0
    
    for a in applications:
        a.verfication_number = a.get_verification_number()
        a.save()

        counter += 1
        if (counter % 100) == 0:
            print(counter)

    print('Updated ',counter,' applications')
        

if __name__ == '__main__':
    main()
    
