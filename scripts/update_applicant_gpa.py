from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant

def main():
    fname = sys.argv[1]

    lines = open(fname).readlines()

    counter = 0
    for l in lines:
        items = l.split(",")
        if len(items) != 2:
            continue
        
        gpa = float(items[1])

        a = Applicant.objects.get(national_id=items[0])
        edu = a.educationalprofile
        old_gpa = edu.gpa
        edu.gpa = gpa
        edu.save()

        print(a,old_gpa,gpa)
        
        counter += 1
        
    print(counter,'updated')
            
if __name__ == '__main__':
    main()
