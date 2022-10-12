from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from appl.models import AdmissionRound, Major, MajorInterviewDescription

DESCIPTION_FIELDS = [
    'has_free_acceptance',
    'has_onsite_interview',
    'has_online_interview',
    'has_document_requirements',
    'has_upload_requirements',
]

DESCRIPTION_CHOICES = {
    1: ( True, False, False, False, False),
    2: (False, False,  True, False, False),
    3: (False, False,  True,  True,  True),
    4: (False, False, False,  True,  True),
    5: (False, False, False,  True, False),
    6: (False, False,  True,  True, False),
}

def main():
    filename = sys.argv[1]
    counter = 0
    admission_round = AdmissionRound.objects.get(pk=2)
    
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for items in reader:
            if len(items) < 4:
                continue

            project_id = int(items[0])
            major_number = int(items[1])
            majors = Major.objects.filter(admission_project_id=project_id,
                                         number=major_number)

            if len(majors) == 0:
                print('MAJOR NOT FOUND', major_number)
                continue
            
            major = majors[0]

            old_descs = MajorInterviewDescription.objects.filter(major=major).all()
            if len(old_descs) > 0:
                desc = old_descs[0]
            else:
                desc = MajorInterviewDescription(major=major,
                                                 admission_round=admission_round)

            desc.admission_round=admission_round
            choice = int(items[4])

            for f,v in zip(DESCIPTION_FIELDS, DESCRIPTION_CHOICES[choice]):
                setattr(desc, f, v)

            if desc.has_document_requirements:
                desc.descriptions = items[6].strip()
            else:
                desc.descriptions = ''

            if desc.has_online_interview and desc.descriptions == '':
                desc.descriptions = items[8].strip().replace("’",'"').replace("'",'"')
                if desc.descriptions == '':
                    desc.descriptions = items[6].strip()

            print(desc.descriptions)
            desc.save()
            print(f'{major.admission_project} - {major}')

            counter += 1
        
    print('Imported',counter,'majors')
        

if __name__ == '__main__':
    main()
    
